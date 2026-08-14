from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import TaskEventModel, TaskModel
from app.repositories.tasks import TaskRepository
from app.schemas.tasks import TaskStatus
from app.services.codex_gateway import CodexGateway


class TaskNotFoundError(LookupError):
    pass


class TaskConflictError(RuntimeError):
    pass


class TaskService:
    def __init__(self, session: AsyncSession, gateway: CodexGateway) -> None:
        self.session = session
        self.repo = TaskRepository(session)
        self.gateway = gateway

    async def create_and_run(self, *, goal: str, workspace: str | None) -> TaskModel:
        task = await self.repo.create(goal=goal, workspace=workspace)
        await self.repo.add_event(task.id, "task.created", "Task accepted")
        await self.session.commit()

        task.status = TaskStatus.running.value
        task.error = None
        await self.repo.add_event(task.id, "task.started", "Codex execution started")
        await self.repo.save(task)
        await self.session.commit()

        try:
            result = await self.gateway.start(goal, workspace)
        except Exception as exc:
            task.status = TaskStatus.failed.value
            task.error = str(exc)
            await self.repo.add_event(task.id, "task.failed", task.error)
            await self.repo.save(task)
            await self.session.commit()
            return task

        task.codex_thread_id = result.thread_id
        task.result = result.final_response
        task.status = TaskStatus.completed.value
        task.error = None
        await self.repo.add_event(task.id, "task.completed", "Codex execution completed")
        await self.repo.save(task)
        await self.session.commit()
        return task

    async def get(self, task_id: UUID) -> TaskModel:
        task = await self.repo.get(task_id)
        if task is None:
            raise TaskNotFoundError(str(task_id))
        return task

    async def continue_and_run(self, task_id: UUID, instruction: str) -> TaskModel:
        task = await self.get(task_id)
        if not task.codex_thread_id:
            raise TaskConflictError("Task has no Codex thread")

        task.status = TaskStatus.running.value
        task.error = None
        await self.repo.add_event(task.id, "task.resumed", "Codex thread resumed")
        await self.repo.save(task)
        await self.session.commit()

        try:
            result = await self.gateway.resume(
                task.codex_thread_id,
                instruction,
                task.workspace,
            )
        except Exception as exc:
            task.status = TaskStatus.failed.value
            task.error = str(exc)
            await self.repo.add_event(task.id, "task.failed", task.error)
            await self.repo.save(task)
            await self.session.commit()
            return task

        task.codex_thread_id = result.thread_id
        task.result = result.final_response
        task.status = TaskStatus.completed.value
        task.error = None
        await self.repo.add_event(task.id, "task.completed", "Codex continuation completed")
        await self.repo.save(task)
        await self.session.commit()
        return task

    async def events(self, task_id: UUID) -> list[TaskEventModel]:
        await self.get(task_id)
        return await self.repo.list_events(task_id)
