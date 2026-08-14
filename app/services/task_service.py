from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact import TaskArtifactModel
from app.models.task import TaskEventModel, TaskModel
from app.repositories.artifacts import ArtifactRepository
from app.repositories.tasks import TaskRepository
from app.schemas.tasks import ApprovalStatus, TaskStatus
from app.services.approval_policy import ApprovalPolicy
from app.services.artifact_indexer import ArtifactIndexer
from app.services.codex_gateway import CodexGateway


class TaskNotFoundError(LookupError):
    pass


class TaskConflictError(RuntimeError):
    pass


class TaskService:
    def __init__(
        self,
        session: AsyncSession,
        gateway: CodexGateway,
        approval_policy: ApprovalPolicy | None = None,
        artifact_indexer: ArtifactIndexer | None = None,
    ) -> None:
        self.session = session
        self.repo = TaskRepository(session)
        self.artifact_repo = ArtifactRepository(session)
        self.gateway = gateway
        self.approval_policy = approval_policy or ApprovalPolicy()
        self.artifact_indexer = artifact_indexer

    async def create_and_run(self, *, goal: str, workspace: str | None) -> TaskModel:
        task = await self.repo.create(goal=goal, workspace=workspace)
        await self.repo.add_event(task.id, "task.created", "Task accepted")

        decision = self.approval_policy.evaluate(goal)
        if decision.required:
            task.approval_required = True
            task.approval_status = ApprovalStatus.pending.value
            task.status = TaskStatus.waiting_approval.value
            await self.repo.add_event(task.id, "approval.requested", decision.reason)
            await self.repo.save(task)
            await self.session.commit()
            return task

        await self.session.commit()
        return await self._start(task)

    async def _start(self, task: TaskModel) -> TaskModel:
        task.status = TaskStatus.running.value
        task.error = None
        await self.repo.add_event(task.id, "task.started", "Codex execution started")
        await self.repo.save(task)
        await self.session.commit()

        try:
            result = await self.gateway.start(task.goal, task.workspace)
        except Exception as exc:  # noqa: BLE001 - execution boundary must persist failures
            return await self._fail(task, exc)

        task.codex_thread_id = result.thread_id
        task.result = result.final_response
        task.status = TaskStatus.completed.value
        task.error = None
        await self.repo.add_event(task.id, "task.completed", "Codex execution completed")
        await self.repo.save(task)
        await self.session.commit()
        await self.refresh_artifacts(task)
        return task

    async def _resume(self, task: TaskModel, instruction: str) -> TaskModel:
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
        except Exception as exc:  # noqa: BLE001 - execution boundary must persist failures
            return await self._fail(task, exc)

        task.codex_thread_id = result.thread_id
        task.result = result.final_response
        task.status = TaskStatus.completed.value
        task.error = None
        task.pending_instruction = None
        await self.repo.add_event(task.id, "task.completed", "Codex continuation completed")
        await self.repo.save(task)
        await self.session.commit()
        await self.refresh_artifacts(task)
        return task

    async def refresh_artifacts(self, task: TaskModel) -> None:
        if self.artifact_indexer is None:
            return
        try:
            snapshots = await self.artifact_indexer.scan(task.workspace)
            await self.artifact_repo.replace(task.id, snapshots)
            if snapshots:
                await self.repo.add_event(
                    task.id,
                    "artifacts.indexed",
                    f"Indexed {len(snapshots)} workspace artifacts",
                )
            await self.session.commit()
        except Exception as exc:  # noqa: BLE001 - artifact indexing must not fail the task
            await self.session.rollback()
            await self.session.refresh(task)
            await self.repo.add_event(task.id, "artifacts.index_failed", str(exc))
            await self.session.commit()

    async def _fail(self, task: TaskModel, exc: Exception) -> TaskModel:
        task.status = TaskStatus.failed.value
        task.error = str(exc)
        await self.repo.add_event(task.id, "task.failed", task.error)
        await self.repo.save(task)
        await self.session.commit()
        return task

    async def get(self, task_id: UUID) -> TaskModel:
        task = await self.repo.get(task_id)
        if task is None:
            raise TaskNotFoundError(str(task_id))
        return task

    async def list(
        self,
        *,
        status: TaskStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TaskModel]:
        return await self.repo.list(
            status=status.value if status is not None else None,
            limit=limit,
            offset=offset,
        )

    async def continue_and_run(self, task_id: UUID, instruction: str) -> TaskModel:
        task = await self.get(task_id)
        if not task.codex_thread_id:
            raise TaskConflictError("Task has no Codex thread")

        decision = self.approval_policy.evaluate(instruction)
        if decision.required:
            task.approval_required = True
            task.approval_status = ApprovalStatus.pending.value
            task.pending_instruction = instruction
            task.status = TaskStatus.waiting_approval.value
            await self.repo.add_event(task.id, "approval.requested", decision.reason)
            await self.repo.save(task)
            await self.session.commit()
            return task

        return await self._resume(task, instruction)

    async def approve(self, task_id: UUID, note: str | None = None) -> TaskModel:
        task = await self.get(task_id)
        if (
            task.status != TaskStatus.waiting_approval.value
            or task.approval_status != ApprovalStatus.pending.value
        ):
            raise TaskConflictError("Task is not waiting for approval")

        task.approval_status = ApprovalStatus.approved.value
        await self.repo.add_event(task.id, "approval.approved", note or "Approved")
        await self.repo.save(task)
        await self.session.commit()

        if task.pending_instruction is not None:
            instruction = task.pending_instruction
            return await self._resume(task, instruction)
        return await self._start(task)

    async def reject(self, task_id: UUID, note: str | None = None) -> TaskModel:
        task = await self.get(task_id)
        if (
            task.status != TaskStatus.waiting_approval.value
            or task.approval_status != ApprovalStatus.pending.value
        ):
            raise TaskConflictError("Task is not waiting for approval")

        task.approval_status = ApprovalStatus.rejected.value
        task.status = TaskStatus.cancelled.value
        task.pending_instruction = None
        await self.repo.add_event(task.id, "approval.rejected", note or "Rejected")
        await self.repo.save(task)
        await self.session.commit()
        return task

    async def events(self, task_id: UUID) -> list[TaskEventModel]:
        await self.get(task_id)
        return await self.repo.list_events(task_id)

    async def artifacts(self, task_id: UUID) -> list[TaskArtifactModel]:
        await self.get(task_id)
        return await self.artifact_repo.list(task_id)
