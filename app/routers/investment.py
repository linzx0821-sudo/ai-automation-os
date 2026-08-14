from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.dependencies import InvestmentQueryServiceDep, InvestmentResearchServiceDep
from app.investment.schemas import InvestmentResearchRequest
from app.investment.views import CompanyRecord, FactRecord, FinancialMetricRecord, ThesisRecord
from app.schemas.tasks import TaskRecord

router = APIRouter(prefix="/investment", tags=["investment"])


@router.post("/research", response_model=TaskRecord)
async def research_company(
    payload: InvestmentResearchRequest,
    service: InvestmentResearchServiceDep,
) -> TaskRecord:
    task = await service.research(payload)
    return TaskRecord.model_validate(task)


@router.get("/companies", response_model=list[CompanyRecord])
async def list_companies(
    service: InvestmentQueryServiceDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[CompanyRecord]:
    companies = await service.list_companies(limit=limit, offset=offset)
    return [CompanyRecord.model_validate(company) for company in companies]


@router.get("/companies/{company_id}", response_model=CompanyRecord)
async def get_company(
    company_id: UUID,
    service: InvestmentQueryServiceDep,
) -> CompanyRecord:
    company = await service.get_company(company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyRecord.model_validate(company)


@router.get("/companies/{company_id}/facts", response_model=list[FactRecord])
async def list_company_facts(
    company_id: UUID,
    service: InvestmentQueryServiceDep,
    verification_status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[FactRecord]:
    if await service.get_company(company_id) is None:
        raise HTTPException(status_code=404, detail="Company not found")
    facts = await service.list_facts(
        company_id,
        verification_status=verification_status,
        limit=limit,
        offset=offset,
    )
    return [FactRecord.model_validate(fact) for fact in facts]


@router.get("/companies/{company_id}/metrics", response_model=list[FinancialMetricRecord])
async def list_company_metrics(
    company_id: UUID,
    service: InvestmentQueryServiceDep,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[FinancialMetricRecord]:
    if await service.get_company(company_id) is None:
        raise HTTPException(status_code=404, detail="Company not found")
    metrics = await service.list_metrics(company_id, limit=limit, offset=offset)
    return [FinancialMetricRecord.model_validate(metric) for metric in metrics]


@router.get("/companies/{company_id}/theses", response_model=list[ThesisRecord])
async def list_company_theses(
    company_id: UUID,
    service: InvestmentQueryServiceDep,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ThesisRecord]:
    if await service.get_company(company_id) is None:
        raise HTTPException(status_code=404, detail="Company not found")
    theses = await service.list_theses(
        company_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [ThesisRecord.model_validate(thesis) for thesis in theses]
