"""Add Investment OS evidence and thesis memory.

Revision ID: 20260814_0003
Revises: 20260814_0002
Create Date: 2026-08-14
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260814_0003"
down_revision: str | Sequence[str] | None = "20260814_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("ticker", sa.String(length=40), nullable=False),
        sa.Column("exchange", sa.String(length=80), nullable=False),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("currency", sa.String(length=12), nullable=True),
        sa.Column("sector", sa.String(length=200), nullable=True),
        sa.Column("industry", sa.String(length=200), nullable=True),
        sa.Column("fiscal_year_end", sa.String(length=10), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker", "exchange", name="uq_companies_ticker_exchange"),
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("document_type", sa.String(length=80), nullable=False),
        sa.Column("source_type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=1000), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reporting_period", sa.String(length=80), nullable=True),
        sa.Column("content_sha256", sa.String(length=64), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_documents_company_id", "documents", ["company_id"], unique=False)
    op.create_index("ix_documents_document_type", "documents", ["document_type"], unique=False)
    op.create_index("ix_documents_content_sha256", "documents", ["content_sha256"], unique=False)

    op.create_table(
        "facts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=True),
        sa.Column("metric", sa.String(length=200), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("value_numeric", sa.Numeric(precision=38, scale=12), nullable=True),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("currency", sa.String(length=12), nullable=True),
        sa.Column("unit", sa.String(length=40), nullable=True),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_quote", sa.Text(), nullable=True),
        sa.Column("source_location", sa.String(length=500), nullable=True),
        sa.Column("confidence", sa.String(length=16), nullable=False),
        sa.Column("verification_status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_facts_company_id", "facts", ["company_id"], unique=False)
    op.create_index("ix_facts_document_id", "facts", ["document_id"], unique=False)
    op.create_index("ix_facts_metric", "facts", ["metric"], unique=False)
    op.create_index("ix_facts_period_end", "facts", ["period_end"], unique=False)
    op.create_index("ix_facts_verification_status", "facts", ["verification_status"], unique=False)

    op.create_table(
        "fact_sources",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("fact_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("reported_value_numeric", sa.Numeric(precision=38, scale=12), nullable=True),
        sa.Column("reported_value_text", sa.Text(), nullable=True),
        sa.Column("variance_ratio", sa.Numeric(precision=20, scale=12), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["fact_id"], ["facts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fact_id", "document_id", name="uq_fact_sources_fact_document"),
    )
    op.create_index("ix_fact_sources_fact_id", "fact_sources", ["fact_id"], unique=False)
    op.create_index("ix_fact_sources_document_id", "fact_sources", ["document_id"], unique=False)

    op.create_table(
        "financial_metrics",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("metric", sa.String(length=200), nullable=False),
        sa.Column("value_numeric", sa.Numeric(precision=38, scale=12), nullable=False),
        sa.Column("currency", sa.String(length=12), nullable=True),
        sa.Column("unit", sa.String(length=40), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("formula", sa.Text(), nullable=False),
        sa.Column("formula_version", sa.String(length=40), nullable=False),
        sa.Column("input_fact_ids", sa.JSON(), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_financial_metrics_company_id", "financial_metrics", ["company_id"], unique=False)
    op.create_index("ix_financial_metrics_metric", "financial_metrics", ["metric"], unique=False)
    op.create_index("ix_financial_metrics_period_end", "financial_metrics", ["period_end"], unique=False)

    op.create_table(
        "investment_theses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("evidence_fact_ids", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_investment_theses_company_id", "investment_theses", ["company_id"], unique=False)
    op.create_index("ix_investment_theses_status", "investment_theses", ["status"], unique=False)

    op.create_table(
        "thesis_conditions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("thesis_id", sa.Uuid(), nullable=False),
        sa.Column("condition_type", sa.String(length=32), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("metric", sa.String(length=200), nullable=True),
        sa.Column("operator", sa.String(length=16), nullable=True),
        sa.Column("threshold_numeric", sa.Numeric(precision=38, scale=12), nullable=True),
        sa.Column("unit", sa.String(length=40), nullable=True),
        sa.Column("consecutive_periods", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("last_evaluated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["thesis_id"], ["investment_theses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_thesis_conditions_thesis_id", "thesis_conditions", ["thesis_id"], unique=False)
    op.create_index("ix_thesis_conditions_status", "thesis_conditions", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_thesis_conditions_status", table_name="thesis_conditions")
    op.drop_index("ix_thesis_conditions_thesis_id", table_name="thesis_conditions")
    op.drop_table("thesis_conditions")
    op.drop_index("ix_investment_theses_status", table_name="investment_theses")
    op.drop_index("ix_investment_theses_company_id", table_name="investment_theses")
    op.drop_table("investment_theses")
    op.drop_index("ix_financial_metrics_period_end", table_name="financial_metrics")
    op.drop_index("ix_financial_metrics_metric", table_name="financial_metrics")
    op.drop_index("ix_financial_metrics_company_id", table_name="financial_metrics")
    op.drop_table("financial_metrics")
    op.drop_index("ix_fact_sources_document_id", table_name="fact_sources")
    op.drop_index("ix_fact_sources_fact_id", table_name="fact_sources")
    op.drop_table("fact_sources")
    op.drop_index("ix_facts_verification_status", table_name="facts")
    op.drop_index("ix_facts_period_end", table_name="facts")
    op.drop_index("ix_facts_metric", table_name="facts")
    op.drop_index("ix_facts_document_id", table_name="facts")
    op.drop_index("ix_facts_company_id", table_name="facts")
    op.drop_table("facts")
    op.drop_index("ix_documents_content_sha256", table_name="documents")
    op.drop_index("ix_documents_document_type", table_name="documents")
    op.drop_index("ix_documents_company_id", table_name="documents")
    op.drop_table("documents")
    op.drop_table("companies")
