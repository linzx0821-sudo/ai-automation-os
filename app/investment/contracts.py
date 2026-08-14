# ruff: noqa: I001
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


Confidence = Literal["high", "medium", "low", "unknown"]
VerificationStatus = Literal["unverified", "verified", "conflict", "insufficient"]


class ResearchCompany(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    ticker: str = Field(min_length=1, max_length=40)
    exchange: str = Field(min_length=1, max_length=80)
    country: str | None = None
    currency: str | None = Field(default=None, max_length=12)
    sector: str | None = None
    industry: str | None = None
    fiscal_year_end: str | None = Field(default=None, max_length=10)


class EvidenceDocument(BaseModel):
    key: str = Field(min_length=1, max_length=100)
    document_type: str = Field(min_length=1, max_length=80)
    source_type: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=1000)
    source_url: HttpUrl
    published_at: datetime | None = None
    reporting_period: str | None = None
    content_sha256: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{64}$")
    metadata: dict[str, object] = Field(default_factory=dict)


class EvidenceSource(BaseModel):
    document_key: str = Field(min_length=1, max_length=100)
    reported_value_numeric: Decimal | None = None
    reported_value_text: str | None = None
    variance_ratio: Decimal | None = None
    status: Literal["supporting", "conflicting", "context"] = "supporting"


class EvidenceFact(BaseModel):
    key: str = Field(min_length=1, max_length=100)
    metric: str = Field(min_length=1, max_length=200)
    statement: str = Field(min_length=1)
    primary_document_key: str | None = Field(default=None, max_length=100)
    value_numeric: Decimal | None = None
    value_text: str | None = None
    currency: str | None = Field(default=None, max_length=12)
    unit: str | None = Field(default=None, max_length=40)
    period_start: date | None = None
    period_end: date | None = None
    as_of: datetime | None = None
    source_quote: str | None = None
    source_location: str | None = Field(default=None, max_length=500)
    confidence: Confidence = "unknown"
    verification_status: VerificationStatus = "unverified"
    sources: list[EvidenceSource] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_a_value_or_statement_only(self) -> "EvidenceFact":
        if self.value_numeric is not None and self.value_text is not None:
            raise ValueError("Fact cannot contain both value_numeric and value_text")
        return self


class EvidenceArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    generated_at: datetime
    company: ResearchCompany
    documents: list[EvidenceDocument]
    facts: list[EvidenceFact]

    @model_validator(mode="after")
    def validate_references(self) -> "EvidenceArtifact":
        document_keys = [document.key for document in self.documents]
        if len(document_keys) != len(set(document_keys)):
            raise ValueError("Duplicate document keys")
        fact_keys = [fact.key for fact in self.facts]
        if len(fact_keys) != len(set(fact_keys)):
            raise ValueError("Duplicate fact keys")
        documents = set(document_keys)
        for fact in self.facts:
            if fact.primary_document_key and fact.primary_document_key not in documents:
                raise ValueError(f"Unknown primary document: {fact.primary_document_key}")
            for source in fact.sources:
                if source.document_key not in documents:
                    raise ValueError(f"Unknown source document: {source.document_key}")
        return self


class CalculatedMetric(BaseModel):
    metric: str = Field(min_length=1, max_length=200)
    value_numeric: Decimal
    currency: str | None = Field(default=None, max_length=12)
    unit: str | None = Field(default=None, max_length=40)
    period_end: date | None = None
    formula: str = Field(min_length=1)
    formula_version: str = Field(min_length=1, max_length=40)
    input_fact_keys: list[str] = Field(default_factory=list)


class MetricsArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    metrics: list[CalculatedMetric]


class ThesisConditionArtifact(BaseModel):
    condition_type: Literal["strengthen", "weaken", "invalidate", "monitor"]
    description: str = Field(min_length=1)
    metric: str | None = Field(default=None, max_length=200)
    operator: Literal[">", ">=", "<", "<=", "==", "!="] | None = None
    threshold_numeric: Decimal | None = None
    unit: str | None = Field(default=None, max_length=40)
    consecutive_periods: int | None = Field(default=None, ge=1, le=40)


class ThesisArtifactItem(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    statement: str = Field(min_length=1)
    status: Literal["active", "strengthened", "weakened", "invalidated", "unknown"] = "active"
    confidence: Decimal | None = Field(default=None, ge=Decimal(0), le=Decimal(1))
    evidence_fact_keys: list[str] = Field(default_factory=list)
    conditions: list[ThesisConditionArtifact] = Field(default_factory=list)


class ThesisArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    theses: list[ThesisArtifactItem]
