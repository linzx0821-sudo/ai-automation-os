import json
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import Base
from app.investment.memory import ResearchArtifactImporter
from app.models.investment import (
    CompanyModel,
    DocumentModel,
    FactModel,
    FinancialMetricModel,
    InvestmentThesisModel,
    ThesisConditionModel,
)


@pytest.mark.asyncio
async def test_research_artifacts_import_into_investment_memory(tmp_path) -> None:
    workspace = tmp_path / "investment" / "tencent"
    research = workspace / "research"
    research.mkdir(parents=True)

    (research / "evidence.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "generated_at": "2026-08-14T12:00:00+08:00",
                "company": {
                    "name": "Tencent Holdings",
                    "ticker": "0700",
                    "exchange": "HKEX",
                    "country": "China",
                    "currency": "HKD",
                },
                "documents": [
                    {
                        "key": "annual-report",
                        "document_type": "annual_report",
                        "source_type": "company_filing",
                        "title": "Annual Report",
                        "source_url": "https://example.com/annual-report.pdf",
                        "published_at": "2026-03-20T00:00:00+08:00",
                        "reporting_period": "FY2025",
                    },
                    {
                        "key": "exchange-filing",
                        "document_type": "exchange_filing",
                        "source_type": "exchange",
                        "title": "Exchange Filing",
                        "source_url": "https://example.com/exchange-filing.pdf",
                    },
                ],
                "facts": [
                    {
                        "key": "revenue-fy2025",
                        "metric": "revenue",
                        "statement": "FY2025 revenue was 1000 HKD million.",
                        "primary_document_key": "annual-report",
                        "value_numeric": "1000",
                        "currency": "HKD",
                        "unit": "million",
                        "period_end": "2025-12-31",
                        "confidence": "high",
                        "verification_status": "verified",
                        "sources": [
                            {
                                "document_key": "annual-report",
                                "reported_value_numeric": "1000",
                            },
                            {
                                "document_key": "exchange-filing",
                                "reported_value_numeric": "1000",
                            },
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (research / "metrics.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "metrics": [
                    {
                        "metric": "operating_margin",
                        "value_numeric": "0.25",
                        "unit": "ratio",
                        "period_end": "2025-12-31",
                        "formula": "operating_income / revenue",
                        "formula_version": "1.0",
                        "input_fact_keys": ["revenue-fy2025"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (research / "thesis.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "theses": [
                    {
                        "title": "Core platform remains durable",
                        "statement": "The core platform remains strategically important.",
                        "status": "active",
                        "confidence": "0.8",
                        "evidence_fact_keys": ["revenue-fy2025"],
                        "conditions": [
                            {
                                "condition_type": "invalidate",
                                "description": "Sustained structural deterioration",
                                "metric": "revenue_growth",
                                "operator": "<",
                                "threshold_numeric": "0",
                                "unit": "ratio",
                                "consecutive_periods": 2,
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        summary = await ResearchArtifactImporter(root=tmp_path).import_workspace(
            session,
            "investment/tencent",
        )
        assert summary.documents == 2
        assert summary.facts == 1
        assert summary.metrics == 1
        assert summary.theses == 1

        assert await session.scalar(select(func.count()).select_from(CompanyModel)) == 1
        assert await session.scalar(select(func.count()).select_from(DocumentModel)) == 2
        assert await session.scalar(select(func.count()).select_from(FactModel)) == 1
        assert await session.scalar(select(func.count()).select_from(FinancialMetricModel)) == 1
        assert await session.scalar(select(func.count()).select_from(InvestmentThesisModel)) == 1
        assert await session.scalar(select(func.count()).select_from(ThesisConditionModel)) == 1

        metric = await session.scalar(select(FinancialMetricModel))
        assert metric is not None
        assert metric.value_numeric == Decimal("0.250000000000")
        assert len(metric.input_fact_ids) == 1

    await engine.dispose()
