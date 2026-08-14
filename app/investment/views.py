from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CompanyRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    ticker: str
    exchange: str
    country: str | None
    currency: str | None
    sector: str | None
    industry: str | None
    fiscal_year_end: str | None
    created_at: datetime
    updated_at: datetime


class FactRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    document_id: UUID | None
    metric: str
    statement: str
    value_numeric: Decimal | None
    value_text: str | None
    currency: str | None
    unit: str | None
    period_start: date | None
    period_end: date | None
    as_of: datetime | None
    source_location: str | None
    confidence: str
    verification_status: str
    created_at: datetime


class FinancialMetricRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    metric: str
    value_numeric: Decimal
    currency: str | None
    unit: str | None
    period_end: date | None
    formula: str
    formula_version: str
    input_fact_ids: list[str]
    calculated_at: datetime


class ThesisConditionRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    condition_type: str
    description: str
    metric: str | None
    operator: str | None
    threshold_numeric: Decimal | None
    unit: str | None
    consecutive_periods: int | None
    status: str
    last_evaluated_at: datetime | None


class ThesisRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    title: str
    statement: str
    status: str
    confidence: Decimal | None
    evidence_fact_ids: list[str]
    created_at: datetime
    updated_at: datetime
    conditions: list[ThesisConditionRecord]
