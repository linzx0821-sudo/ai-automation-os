from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.investment import (
    CompanyModel,
    FactModel,
    FinancialMetricModel,
    InvestmentThesisModel,
)


class InvestmentQueryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_companies(self, limit: int = 100, offset: int = 0) -> list[CompanyModel]:
        statement = (
            select(CompanyModel)
            .order_by(CompanyModel.name, CompanyModel.exchange, CompanyModel.ticker)
            .offset(offset)
            .limit(limit)
        )
        return list((await self.session.scalars(statement)).all())

    async def get_company(self, company_id: UUID) -> CompanyModel | None:
        return await self.session.get(CompanyModel, company_id)

    async def list_facts(
        self,
        company_id: UUID,
        *,
        verification_status: str | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[FactModel]:
        statement = select(FactModel).where(FactModel.company_id == company_id)
        if verification_status is not None:
            statement = statement.where(FactModel.verification_status == verification_status)
        statement = (
            statement.order_by(FactModel.period_end.desc(), FactModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list((await self.session.scalars(statement)).all())

    async def list_metrics(
        self,
        company_id: UUID,
        *,
        limit: int = 200,
        offset: int = 0,
    ) -> list[FinancialMetricModel]:
        statement = (
            select(FinancialMetricModel)
            .where(FinancialMetricModel.company_id == company_id)
            .order_by(
                FinancialMetricModel.period_end.desc(),
                FinancialMetricModel.calculated_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        return list((await self.session.scalars(statement)).all())

    async def list_theses(
        self,
        company_id: UUID,
        *,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[InvestmentThesisModel]:
        statement = (
            select(InvestmentThesisModel)
            .options(selectinload(InvestmentThesisModel.conditions))
            .where(InvestmentThesisModel.company_id == company_id)
        )
        if status is not None:
            statement = statement.where(InvestmentThesisModel.status == status)
        statement = (
            statement.order_by(InvestmentThesisModel.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list((await self.session.scalars(statement)).all())
