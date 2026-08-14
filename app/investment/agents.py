import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

from agents import Agent, Runner

from app.investment.agent_models import CommitteeDecision, SpecialistAssessment
from app.investment.contracts import (
    EvidenceArtifact,
    MetricsArtifact,
    ThesisArtifact,
    ThesisArtifactItem,
    ThesisConditionArtifact,
)
from app.investment.memory import ResearchArtifactImportError


@dataclass(frozen=True, slots=True)
class SpecialistSpec:
    name: str
    perspective: str
    mandate: str


SPECIALISTS = (
    SpecialistSpec(
        name="Business Model Analyst",
        perspective="business_model",
        mandate=(
            "Assess how the company creates value, who pays, recurring economics, customer "
            "dependency, business quality, and whether the economics are understandable."
        ),
    ),
    SpecialistSpec(
        name="Moat and Competition Analyst",
        perspective="moat_competition",
        mandate=(
            "Assess durable competitive advantages, switching costs, network effects, scale, "
            "distribution, substitutes, competitive response, and moat erosion."
        ),
    ),
    SpecialistSpec(
        name="Financial Quality Analyst",
        perspective="financial_quality",
        mandate=(
            "Assess earnings quality, cash conversion, margins, capital intensity, balance-sheet "
            "resilience, reinvestment economics, and consistency. Do not perform mental arithmetic."
        ),
    ),
    SpecialistSpec(
        name="Management and Capital Allocation Analyst",
        perspective="management_capital_allocation",
        mandate=(
            "Assess governance, incentives, candor, capital allocation, dilution, buybacks, M&A, "
            "and evidence of management acting for long-term owners."
        ),
    ),
    SpecialistSpec(
        name="Industry Structure Analyst",
        perspective="industry_structure",
        mandate=(
            "Assess industry economics, bargaining power, regulation, cyclicality, structural "
            "growth or decline, bottlenecks, and threats from adjacent competitors."
        ),
    ),
    SpecialistSpec(
        name="Valuation Readiness Analyst",
        perspective="valuation_readiness",
        mandate=(
            "Assess whether the evidence and deterministic metrics are sufficient for valuation, "
            "which assumptions matter most, and where false precision would be dangerous."
        ),
    ),
    SpecialistSpec(
        name="Bear and Inversion Analyst",
        perspective="bear_inversion",
        mandate=(
            "Build the strongest evidence-based bear case. Identify failure modes, thesis "
            "invalidation paths, hidden dependencies, and plausible reasons the consensus is wrong."
        ),
    ),
    SpecialistSpec(
        name="Evidence Auditor",
        perspective="evidence_audit",
        mandate=(
            "Audit source coverage, fact verification, freshness, units/currencies, conflicts, "
            "unknowns, and whether conclusions overreach the supplied evidence."
        ),
    ),
)


@dataclass(frozen=True, slots=True)
class MultiAgentResearchResult:
    specialists: list[SpecialistAssessment]
    committee: CommitteeDecision


class InvestmentAgentOrchestrator:
    def __init__(self, model: str | None = None, max_turns: int = 6) -> None:
        self.model = model
        self.max_turns = max_turns

    async def run_workspace(self, workspace_root: Path, workspace: str | None) -> MultiAgentResearchResult:
        research_dir = self._research_dir(workspace_root, workspace)
        evidence = self._load(research_dir / "evidence.json", EvidenceArtifact)
        metrics = self._load(research_dir / "metrics.json", MetricsArtifact)
        result = await self.run(evidence, metrics)
        self._write_outputs(research_dir, result)
        return result

    async def run(
        self,
        evidence: EvidenceArtifact,
        metrics: MetricsArtifact,
    ) -> MultiAgentResearchResult:
        shared_input = self._shared_input(evidence, metrics)
        assessments = await asyncio.gather(
            *(self._run_specialist(spec, shared_input) for spec in SPECIALISTS)
        )
        self._validate_specialist_references(assessments, evidence)
        committee = await self._run_committee(evidence, metrics, assessments)
        self._validate_committee_references(committee, evidence)
        return MultiAgentResearchResult(specialists=list(assessments), committee=committee)

    async def _run_specialist(
        self,
        spec: SpecialistSpec,
        shared_input: str,
    ) -> SpecialistAssessment:
        kwargs: dict[str, object] = {
            "name": spec.name,
            "instructions": self._specialist_instructions(spec),
            "output_type": SpecialistAssessment,
        }
        if self.model:
            kwargs["model"] = self.model
        agent = Agent(**kwargs)
        result = await Runner.run(agent, input=shared_input, max_turns=self.max_turns)
        assessment = result.final_output_as(SpecialistAssessment, raise_if_incorrect_type=True)
        if assessment.perspective != spec.perspective:
            raise ResearchArtifactImportError(
                f"Agent {spec.name} returned perspective={assessment.perspective}; "
                f"expected {spec.perspective}"
            )
        return assessment

    async def _run_committee(
        self,
        evidence: EvidenceArtifact,
        metrics: MetricsArtifact,
        assessments: list[SpecialistAssessment],
    ) -> CommitteeDecision:
        kwargs: dict[str, object] = {
            "name": "Investment Research Committee",
            "instructions": self._committee_instructions(),
            "output_type": CommitteeDecision,
        }
        if self.model:
            kwargs["model"] = self.model
        agent = Agent(**kwargs)
        committee_input = json.dumps(
            {
                "company": evidence.company.model_dump(mode="json"),
                "facts": [fact.model_dump(mode="json") for fact in evidence.facts],
                "metrics": [metric.model_dump(mode="json") for metric in metrics.metrics],
                "specialist_assessments": [
                    assessment.model_dump(mode="json") for assessment in assessments
                ],
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        result = await Runner.run(agent, input=committee_input, max_turns=self.max_turns)
        return result.final_output_as(CommitteeDecision, raise_if_incorrect_type=True)

    @staticmethod
    def _specialist_instructions(spec: SpecialistSpec) -> str:
        return f"""You are the {spec.name} in an evidence-first investment research system.

Perspective identifier: {spec.perspective}
Mandate: {spec.mandate}

Rules:
- Analyze ONLY the supplied evidence ledger and deterministic metrics. Do not browse and do not
  introduce facts from memory.
- Every claim marked kind=fact must cite one or more supplied evidence_fact_keys.
- Inferences and assumptions must be labeled honestly. Unknowns must stay unknown.
- Never invent a source, quote, price, financial value, management statement, or fact key.
- Do not perform mental arithmetic. Treat supplied calculated metrics as the only calculated values.
- Surface evidence conflicts and missing data instead of smoothing them over.
- Use a 0..5 score only if the evidence supports a score; otherwise set score=null.
- Return perspective exactly as: {spec.perspective}
- This is research, not a brokerage instruction. Do not tell the user to buy, sell, or place a trade.
"""

    @staticmethod
    def _committee_instructions() -> str:
        return """You are the Investment Research Committee. You receive a verified evidence ledger,
deterministic metrics, and independent specialist assessments.

Rules:
- Synthesize; do not invent new facts.
- Preserve material disagreements instead of averaging them away.
- A thesis may cite only supplied fact keys. If support is weak, mark the thesis unknown or lower
  confidence rather than filling gaps.
- Separate reasons for and against the thesis. Explicitly list unknowns and next evidence needed.
- Invalidation conditions must be concrete and decision-relevant, not generic risk boilerplate.
- research_passed means the evidence is strong enough to maintain a research thesis, not that a
  security should be purchased. needs_more_evidence means important questions block a reliable
  thesis. inconclusive means the evidence supports materially conflicting interpretations.
- Do not tell the user to buy, sell, size a position, or execute a trade.
"""

    @staticmethod
    def _shared_input(evidence: EvidenceArtifact, metrics: MetricsArtifact) -> str:
        return json.dumps(
            {
                "company": evidence.company.model_dump(mode="json"),
                "documents": [document.model_dump(mode="json") for document in evidence.documents],
                "facts": [fact.model_dump(mode="json") for fact in evidence.facts],
                "metrics": [metric.model_dump(mode="json") for metric in metrics.metrics],
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )

    @staticmethod
    def _validate_specialist_references(
        assessments: list[SpecialistAssessment],
        evidence: EvidenceArtifact,
    ) -> None:
        valid = {fact.key for fact in evidence.facts}
        for assessment in assessments:
            for claim in assessment.claims:
                unknown = set(claim.evidence_fact_keys) - valid
                if unknown:
                    raise ResearchArtifactImportError(
                        f"{assessment.perspective} references unknown fact keys: {sorted(unknown)}"
                    )

    @staticmethod
    def _validate_committee_references(
        committee: CommitteeDecision,
        evidence: EvidenceArtifact,
    ) -> None:
        valid = {fact.key for fact in evidence.facts}
        for thesis in committee.theses:
            unknown = set(thesis.evidence_fact_keys) - valid
            if unknown:
                raise ResearchArtifactImportError(
                    f"Committee thesis {thesis.title} references unknown fact keys: {sorted(unknown)}"
                )

    @staticmethod
    def _research_dir(root: Path, workspace: str | None) -> Path:
        if not workspace:
            raise ResearchArtifactImportError("Investment task has no workspace")
        resolved_root = root.expanduser().resolve()
        raw = Path(workspace)
        if raw.is_absolute():
            raise ResearchArtifactImportError("Workspace must be relative")
        workspace_path = (resolved_root / raw).resolve()
        if not workspace_path.is_relative_to(resolved_root):
            raise ResearchArtifactImportError("Workspace escapes configured root")
        research_dir = workspace_path / "research"
        if not research_dir.is_dir():
            raise ResearchArtifactImportError("Research output directory is missing")
        return research_dir

    @staticmethod
    def _load(path: Path, contract_type: type[EvidenceArtifact | MetricsArtifact]):
        if not path.is_file():
            raise ResearchArtifactImportError(f"Required research artifact is missing: {path.name}")
        try:
            return contract_type.model_validate_json(path.read_bytes())
        except Exception as exc:
            raise ResearchArtifactImportError(f"Invalid {path.name}: {exc}") from exc

    def _write_outputs(self, research_dir: Path, result: MultiAgentResearchResult) -> None:
        analysis_payload = {
            "schema_version": "1.0",
            "specialists": [assessment.model_dump(mode="json") for assessment in result.specialists],
            "committee": result.committee.model_dump(mode="json"),
        }
        self._atomic_write_json(research_dir / "agent_analysis.json", analysis_payload)

        thesis_artifact = ThesisArtifact(
            theses=[
                ThesisArtifactItem(
                    title=thesis.title,
                    statement=thesis.statement,
                    status=thesis.status,
                    confidence=thesis.confidence,
                    evidence_fact_keys=thesis.evidence_fact_keys,
                    conditions=[
                        *[
                            ThesisConditionArtifact(
                                condition_type="invalidate",
                                description=description,
                            )
                            for description in thesis.invalidation_conditions
                        ],
                        *[
                            ThesisConditionArtifact(
                                condition_type="monitor",
                                description=description,
                            )
                            for description in thesis.monitor_items
                        ],
                    ],
                )
                for thesis in result.committee.theses
            ]
        )
        self._atomic_write_json(
            research_dir / "thesis.json",
            thesis_artifact.model_dump(mode="json"),
        )
        self._atomic_write_text(research_dir / "report.md", self._render_report(result))

    @staticmethod
    def _render_report(result: MultiAgentResearchResult) -> str:
        committee = result.committee
        lines = [
            "# Investment Research Committee Report",
            "",
            f"**Status:** {committee.status}",
            f"**Confidence:** {committee.confidence}",
            "",
            "## Conclusion",
            committee.one_line_conclusion,
            "",
            "## Reasons For",
            *[f"- {item}" for item in committee.reasons_for],
            "",
            "## Reasons Against",
            *[f"- {item}" for item in committee.reasons_against],
            "",
            "## Material Disagreements",
            *[f"- {item}" for item in committee.disagreements],
            "",
            "## Unknowns",
            *[f"- {item}" for item in committee.unknowns],
            "",
            "## Next Evidence To Collect",
            *[f"- {item}" for item in committee.next_evidence_to_collect],
            "",
            "## Specialist Views",
        ]
        for assessment in result.specialists:
            lines.extend(
                [
                    "",
                    f"### {assessment.perspective}",
                    f"- Score: {assessment.score if assessment.score is not None else 'N/A'} / 5",
                    f"- Confidence: {assessment.confidence}",
                    f"- Conclusion: {assessment.conclusion}",
                ]
            )
        lines.extend(
            [
                "",
                "---",
                "Research only. This report does not instruct or execute a securities transaction.",
                "",
            ]
        )
        return "\n".join(lines)

    @staticmethod
    def _atomic_write_json(path: Path, payload: object) -> None:
        text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        InvestmentAgentOrchestrator._atomic_write_text(path, text)

    @staticmethod
    def _atomic_write_text(path: Path, text: str) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(path)
