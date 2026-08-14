from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.investment.contracts import EvidenceArtifact, MetricsArtifact, ThesisArtifact
from app.models.investment import (
    CompanyModel,
    DocumentModel,
    FactModel,
    FactSourceModel,
    FinancialMetricModel,
    InvestmentThesisModel,
    ThesisConditionModel,
)


class ResearchArtifactImportError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ResearchImportSummary:
    company_id: UUID
    documents: int
    facts: int
    metrics: int
    theses: int


@dataclass(slots=True)
class ResearchArtifactImporter:
    root: Path
    max_json_bytes: int = 20 * 1024 * 1024

    async def import_workspace(
        self,
        session: AsyncSession,
        workspace: str | None,
    ) -> ResearchImportSummary:
        research_dir = self._resolve_research_dir(workspace)
        evidence = self._load_contract(research_dir / "evidence.json", EvidenceArtifact)
        metrics = self._load_contract(research_dir / "metrics.json", MetricsArtifact)
        theses = self._load_contract(research_dir / "thesis.json", ThesisArtifact)

        company = await self._upsert_company(session, evidence)
        document_ids = await self._upsert_documents(session, company.id, evidence)
        fact_ids = await self._insert_facts(session, company.id, evidence, document_ids)
        await self._insert_metrics(session, company.id, metrics, fact_ids)
        await self._insert_theses(session, company.id, theses, fact_ids)
        await session.commit()

        return ResearchImportSummary(
            company_id=company.id,
            documents=len(evidence.documents),
            facts=len(evidence.facts),
            metrics=len(metrics.metrics),
            theses=len(theses.theses),
        )

    def _resolve_research_dir(self, workspace: str | None) -> Path:
        if not workspace:
            raise ResearchArtifactImportError("Investment task has no workspace")
        root = self.root.expanduser().resolve()
        raw = Path(workspace)
        if raw.is_absolute():
            raise ResearchArtifactImportError("Workspace must be relative")
        workspace_path = (root / raw).resolve()
        if not workspace_path.is_relative_to(root):
            raise ResearchArtifactImportError("Workspace escapes configured root")
        research_dir = workspace_path / "research"
        if not research_dir.is_dir():
            raise ResearchArtifactImportError("Research output directory is missing")
        return research_dir

    def _load_contract(
        self,
        path: Path,
        contract_type: type[EvidenceArtifact | MetricsArtifact | ThesisArtifact],
    ):
        if not path.is_file():
            raise ResearchArtifactImportError(f"Required research artifact is missing: {path.name}")
        if path.stat().st_size > self.max_json_bytes:
            raise ResearchArtifactImportError(f"Research artifact exceeds size limit: {path.name}")
        try:
            return contract_type.model_validate_json(path.read_bytes())
        except Exception as exc:
            raise ResearchArtifactImportError(f"Invalid {path.name}: {exc}") from exc

    async def _upsert_company(
        self,
        session: AsyncSession,
        evidence: EvidenceArtifact,
    ) -> CompanyModel:
        source = evidence.company
        statement = select(CompanyModel).where(
            CompanyModel.ticker == source.ticker,
            CompanyModel.exchange == source.exchange,
        )
        company = await session.scalar(statement)
        if company is None:
            company = CompanyModel(
                name=source.name,
                ticker=source.ticker,
                exchange=source.exchange,
            )
            session.add(company)
        company.name = source.name
        company.country = source.country
        company.currency = source.currency
        company.sector = source.sector
        company.industry = source.industry
        company.fiscal_year_end = source.fiscal_year_end
        await session.flush()
        return company

    async def _upsert_documents(
        self,
        session: AsyncSession,
        company_id: UUID,
        evidence: EvidenceArtifact,
    ) -> dict[str, UUID]:
        document_ids: dict[str, UUID] = {}
        for source in evidence.documents:
            source_url = str(source.source_url)
            statement = select(DocumentModel).where(
                DocumentModel.company_id == company_id,
                DocumentModel.source_url == source_url,
            )
            if source.content_sha256:
                statement = statement.where(DocumentModel.content_sha256 == source.content_sha256)
            document = await session.scalar(statement.limit(1))
            if document is None:
                document = DocumentModel(
                    company_id=company_id,
                    document_type=source.document_type,
                    source_type=source.source_type,
                    title=source.title,
                    source_url=source_url,
                    published_at=source.published_at,
                    reporting_period=source.reporting_period,
                    content_sha256=source.content_sha256,
                    metadata_json=source.metadata,
                )
                session.add(document)
                await session.flush()
            document_ids[source.key] = document.id
        return document_ids

    async def _insert_facts(
        self,
        session: AsyncSession,
        company_id: UUID,
        evidence: EvidenceArtifact,
        document_ids: dict[str, UUID],
    ) -> dict[str, UUID]:
        fact_ids: dict[str, UUID] = {}
        for source in evidence.facts:
            document_id = (
                document_ids[source.primary_document_key]
                if source.primary_document_key is not None
                else None
            )
            fact = FactModel(
                company_id=company_id,
                document_id=document_id,
                metric=source.metric,
                statement=source.statement,
                value_numeric=source.value_numeric,
                value_text=source.value_text,
                currency=source.currency,
                unit=source.unit,
                period_start=source.period_start,
                period_end=source.period_end,
                as_of=source.as_of,
                source_quote=source.source_quote,
                source_location=source.source_location,
                confidence=source.confidence,
                verification_status=source.verification_status,
            )
            session.add(fact)
            await session.flush()
            fact_ids[source.key] = fact.id

            seen_documents: set[UUID] = set()
            for evidence_source in source.sources:
                source_document_id = document_ids[evidence_source.document_key]
                if source_document_id in seen_documents:
                    continue
                seen_documents.add(source_document_id)
                session.add(
                    FactSourceModel(
                        fact_id=fact.id,
                        document_id=source_document_id,
                        reported_value_numeric=evidence_source.reported_value_numeric,
                        reported_value_text=evidence_source.reported_value_text,
                        variance_ratio=evidence_source.variance_ratio,
                        status=evidence_source.status,
                    )
                )
        await session.flush()
        return fact_ids

    async def _insert_metrics(
        self,
        session: AsyncSession,
        company_id: UUID,
        artifact: MetricsArtifact,
        fact_ids: dict[str, UUID],
    ) -> None:
        for source in artifact.metrics:
            unknown = set(source.input_fact_keys) - set(fact_ids)
            if unknown:
                raise ResearchArtifactImportError(
                    f"Metric {source.metric} references unknown facts: {sorted(unknown)}"
                )
            session.add(
                FinancialMetricModel(
                    company_id=company_id,
                    metric=source.metric,
                    value_numeric=source.value_numeric,
                    currency=source.currency,
                    unit=source.unit,
                    period_end=source.period_end,
                    formula=source.formula,
                    formula_version=source.formula_version,
                    input_fact_ids=[str(fact_ids[key]) for key in source.input_fact_keys],
                )
            )
        await session.flush()

    async def _insert_theses(
        self,
        session: AsyncSession,
        company_id: UUID,
        artifact: ThesisArtifact,
        fact_ids: dict[str, UUID],
    ) -> None:
        for source in artifact.theses:
            unknown = set(source.evidence_fact_keys) - set(fact_ids)
            if unknown:
                raise ResearchArtifactImportError(
                    f"Thesis {source.title} references unknown facts: {sorted(unknown)}"
                )
            thesis = InvestmentThesisModel(
                company_id=company_id,
                title=source.title,
                statement=source.statement,
                status=source.status,
                confidence=source.confidence,
                evidence_fact_ids=[str(fact_ids[key]) for key in source.evidence_fact_keys],
            )
            session.add(thesis)
            await session.flush()
            for condition in source.conditions:
                session.add(
                    ThesisConditionModel(
                        thesis_id=thesis.id,
                        condition_type=condition.condition_type,
                        description=condition.description,
                        metric=condition.metric,
                        operator=condition.operator,
                        threshold_numeric=condition.threshold_numeric,
                        unit=condition.unit,
                        consecutive_periods=condition.consecutive_periods,
                    )
                )
        await session.flush()
