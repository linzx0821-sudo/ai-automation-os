from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.investment.agent_models import (
    AgentClaim,
    CommitteeDecision,
    CommitteeThesis,
    SpecialistAssessment,
)
from app.investment.agents import InvestmentAgentOrchestrator, MultiAgentResearchResult
from app.investment.contracts import EvidenceArtifact, EvidenceFact, ResearchCompany
from app.investment.memory import ResearchArtifactImportError


def _evidence() -> EvidenceArtifact:
    return EvidenceArtifact(
        generated_at=datetime.now(timezone.utc),
        company=ResearchCompany(name="Acme", ticker="ACME", exchange="TEST"),
        documents=[],
        facts=[
            EvidenceFact(
                key="revenue",
                metric="revenue",
                statement="Revenue was reported.",
                value_numeric=Decimal("100"),
                unit="million",
                confidence="high",
                verification_status="verified",
            )
        ],
    )


def test_fact_claim_requires_evidence_reference() -> None:
    with pytest.raises(ValidationError):
        AgentClaim(
            statement="Revenue increased",
            kind="fact",
            evidence_fact_keys=[],
            confidence=Decimal("0.9"),
        )


def test_specialist_unknown_fact_reference_is_rejected() -> None:
    assessment = SpecialistAssessment(
        perspective="business_model",
        confidence=Decimal("0.8"),
        conclusion="Evidence is incomplete.",
        claims=[
            AgentClaim(
                statement="Claim",
                kind="fact",
                evidence_fact_keys=["missing-fact"],
                confidence=Decimal("0.8"),
            )
        ],
    )
    with pytest.raises(ResearchArtifactImportError, match="unknown fact keys"):
        InvestmentAgentOrchestrator._validate_specialist_references([assessment], _evidence())


def test_agent_outputs_are_written_as_valid_research_artifacts(tmp_path) -> None:
    research_dir = tmp_path / "research"
    research_dir.mkdir()
    specialist = SpecialistAssessment(
        perspective="business_model",
        score=Decimal("4"),
        confidence=Decimal("0.8"),
        conclusion="Business evidence is supportive.",
    )
    committee = CommitteeDecision(
        status="research_passed",
        confidence=Decimal("0.75"),
        one_line_conclusion="Evidence supports maintaining a research thesis.",
        reasons_for=["Verified operating evidence"],
        reasons_against=["Limited history"],
        unknowns=["Long-term competitive response"],
        theses=[
            CommitteeThesis(
                title="Core economics",
                statement="Core economics remain durable based on current evidence.",
                status="active",
                confidence=Decimal("0.75"),
                evidence_fact_keys=["revenue"],
                invalidation_conditions=["Sustained structural revenue deterioration"],
                monitor_items=["Revenue quality"],
            )
        ],
    )
    result = MultiAgentResearchResult(specialists=[specialist], committee=committee)

    InvestmentAgentOrchestrator()._write_outputs(research_dir, result)

    assert (research_dir / "agent_analysis.json").is_file()
    assert (research_dir / "report.md").is_file()
    assert (research_dir / "thesis.json").is_file()
    assert "Research only" in (research_dir / "report.md").read_text(encoding="utf-8")
