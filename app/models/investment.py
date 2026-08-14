from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class CompanyModel(Base):
    __tablename__ = "companies"
    __table_args__ = (UniqueConstraint("ticker", "exchange", name="uq_companies_ticker_exchange"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    ticker: Mapped[str] = mapped_column(String(40), nullable=False)
    exchange: Mapped[str] = mapped_column(String(80), nullable=False)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(12), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(200), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(200), nullable=True)
    fiscal_year_end: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    documents: Mapped[list["DocumentModel"]] = relationship(back_populates="company")
    facts: Mapped[list["FactModel"]] = relationship(back_populates="company")
    theses: Mapped[list["InvestmentThesisModel"]] = relationship(back_populates="company")


class DocumentModel(Base):
    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reporting_period: Mapped[str | None] = mapped_column(String(80), nullable=True)
    content_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    company: Mapped[CompanyModel] = relationship(back_populates="documents")
    facts: Mapped[list["FactModel"]] = relationship(back_populates="document")


class FactModel(Base):
    __tablename__ = "facts"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    metric: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    value_numeric: Mapped[Decimal | None] = mapped_column(Numeric(38, 12), nullable=True)
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(12), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    as_of: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_quote: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    confidence: Mapped[str] = mapped_column(String(16), nullable=False, default="unknown")
    verification_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="unverified", index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    company: Mapped[CompanyModel] = relationship(back_populates="facts")
    document: Mapped[DocumentModel | None] = relationship(back_populates="facts")
    sources: Mapped[list["FactSourceModel"]] = relationship(
        back_populates="fact", cascade="all, delete-orphan"
    )


class FactSourceModel(Base):
    __tablename__ = "fact_sources"
    __table_args__ = (UniqueConstraint("fact_id", "document_id", name="uq_fact_sources_fact_document"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fact_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("facts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reported_value_numeric: Mapped[Decimal | None] = mapped_column(Numeric(38, 12), nullable=True)
    reported_value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    variance_ratio: Mapped[Decimal | None] = mapped_column(Numeric(20, 12), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="supporting")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    fact: Mapped[FactModel] = relationship(back_populates="sources")


class FinancialMetricModel(Base):
    __tablename__ = "financial_metrics"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    value_numeric: Mapped[Decimal] = mapped_column(Numeric(38, 12), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(12), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    formula: Mapped[str] = mapped_column(Text, nullable=False)
    formula_version: Mapped[str] = mapped_column(String(40), nullable=False)
    input_fact_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class InvestmentThesisModel(Base):
    __tablename__ = "investment_theses"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    evidence_fact_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    company: Mapped[CompanyModel] = relationship(back_populates="theses")
    conditions: Mapped[list["ThesisConditionModel"]] = relationship(
        back_populates="thesis", cascade="all, delete-orphan"
    )


class ThesisConditionModel(Base):
    __tablename__ = "thesis_conditions"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    thesis_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("investment_theses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    condition_type: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    metric: Mapped[str | None] = mapped_column(String(200), nullable=True)
    operator: Mapped[str | None] = mapped_column(String(16), nullable=True)
    threshold_numeric: Mapped[Decimal | None] = mapped_column(Numeric(38, 12), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    consecutive_periods: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="unresolved", index=True)
    last_evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    thesis: Mapped[InvestmentThesisModel] = relationship(back_populates="conditions")
