from fastapi import APIRouter

from app.dependencies import TaskServiceDep
from app.investment.schemas import InvestmentResearchRequest
from app.investment.workflow import InvestmentResearchWorkflow
from app.schemas.tasks import TaskRecord

router = APIRouter(prefix="/investment", tags=["investment"])
workflow = InvestmentResearchWorkflow()


@router.post("/research", response_model=TaskRecord)
async def research_company(
    payload: InvestmentResearchRequest,
    service: TaskServiceDep,
) -> TaskRecord:
    plan = workflow.plan(payload)
    task = await service.create_and_run(goal=plan.task_goal, workspace=plan.workspace)
    return TaskRecord.model_validate(task)
