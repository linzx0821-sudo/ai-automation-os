from app.investment.memory import ResearchArtifactImporter, ResearchArtifactImportError
from app.investment.schemas import InvestmentResearchRequest
from app.investment.workflow import InvestmentResearchWorkflow
from app.models.task import TaskModel
from app.schemas.tasks import TaskStatus
from app.services.task_service import TaskService


class InvestmentResearchService:
    def __init__(
        self,
        task_service: TaskService,
        importer: ResearchArtifactImporter,
        workflow: InvestmentResearchWorkflow | None = None,
    ) -> None:
        self.task_service = task_service
        self.importer = importer
        self.workflow = workflow or InvestmentResearchWorkflow()

    async def research(self, request: InvestmentResearchRequest) -> TaskModel:
        plan = self.workflow.plan(request)
        task = await self.task_service.create_and_run(
            goal=plan.task_goal,
            workspace=plan.workspace,
        )
        if task.status != TaskStatus.completed.value:
            return task

        # Stub mode intentionally produces no artifacts. It exists only for API/CI testing.
        if task.codex_thread_id and task.codex_thread_id.startswith("stub:"):
            return task

        try:
            summary = await self.importer.import_workspace(
                self.task_service.session,
                task.workspace,
            )
        except ResearchArtifactImportError as exc:
            return await self._mark_memory_failure(task, exc)
        except Exception as exc:  # noqa: BLE001 - trust boundary must persist unexpected failures
            return await self._mark_memory_failure(task, exc)

        await self.task_service.repo.add_event(
            task.id,
            "investment.memory_imported",
            (
                f"company={summary.company_id}; documents={summary.documents}; "
                f"facts={summary.facts}; metrics={summary.metrics}; theses={summary.theses}"
            ),
        )
        await self.task_service.session.commit()
        return task

    async def _mark_memory_failure(self, task: TaskModel, exc: Exception) -> TaskModel:
        await self.task_service.session.rollback()
        refreshed = await self.task_service.get(task.id)
        refreshed.status = TaskStatus.failed.value
        refreshed.error = f"Investment memory import failed: {exc}"
        await self.task_service.repo.add_event(
            refreshed.id,
            "investment.memory_import_failed",
            refreshed.error,
        )
        await self.task_service.repo.save(refreshed)
        await self.task_service.session.commit()
        return refreshed
