from fastapi import APIRouter

from app.dependencies import InvestmentResearchServiceDep
from app.investment.schemas import InvestmentResearchRequest
from app.schemas.tasks import TaskRecord

router = APIRouter(prefix="/investment", tags=["investment"])


@router.post("/research", response_model=TaskRecord)
async def research_company(
    payload: InvestmentResearchRequest,
    service: InvestmentResearchServiceDep,
) -> TaskRecord:
    task = await service.research(payload)
    return TaskRecord.model_validate(task)
