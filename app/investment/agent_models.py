# ruff: noqa: I001
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ClaimKind = Literal["fact", "inference", "assumption", "unknown"]
ResearchStatus = Literal["research_passed", "needs_more_evidence", "inconclusive"]


class AgentClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    statement: str = Field(min_length=1)
    kind: ClaimKind
    evidence_fact_keys: list[str] = Field(default_factory=list)
    confidence: Decimal = Field(ge=Decimal(0), le=Decimal(1))

    @model_validator(mode="after")
    def evidence_rules(self) -> "AgentClaim":
        if self.kind == "fact" and not self.evidence_fact_keys:
            raise ValueError("Fact claims require at least one evidence_fact_key")
        if self.kind == "unknown" and self.evidence_fact_keys:
            raise ValueError("Unknown claims cannot cite evidence as if established")
        return self


class SpecialistAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    perspective: str = Field(min_length=1, max_length=100)
    score: Decimal | None = Field(default=None, ge=Decimal(0), le=Decimal(5))
    confidence: Decimal = Field(ge=Decimal(0), le=Decimal(1))
    conclusion: str = Field(min_length=1)
    claims: list[AgentClaim] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    challenge_questions: list[str] = Field(default_factory=list)


class CommitteeThesis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=500)
    statement: str = Field(min_length=1)
    status: Literal["active", "strengthened", "weakened", "invalidated", "unknown"]
    confidence: Decimal | None = Field(default=None, ge=Decimal(0), le=Decimal(1))
    evidence_fact_keys: list[str] = Field(default_factory=list)
    invalidation_conditions: list[str] = Field(default_factory=list)
    monitor_items: list[str] = Field(default_factory=list)


class CommitteeDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ResearchStatus
    confidence: Decimal = Field(ge=Decimal(0), le=Decimal(1))
    one_line_conclusion: str = Field(min_length=1)
    agreements: list[str] = Field(default_factory=list)
    disagreements: list[str] = Field(default_factory=list)
    reasons_for: list[str] = Field(default_factory=list)
    reasons_against: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    theses: list[CommitteeThesis] = Field(default_factory=list)
    next_evidence_to_collect: list[str] = Field(default_factory=list)
