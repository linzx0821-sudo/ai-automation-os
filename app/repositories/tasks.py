from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import TaskEventModel, TaskModel


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, goal: str, workspace: str | None) -> TaskModel:
        task = TaskModel(goal=goal, workspace=workspace, status="queued")
        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def get(self, task_id: UUID) -> TaskModel | None:
        return await self.session.get(TaskModel, task_id)

    async def list(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TaskModel]:
        statement = select(TaskModel)
        if status is not None:
            statement = statement.where(TaskModel.status == status)
        statement = (
            statement.order_by(TaskModel.created_at.desc(), TaskModel.id)
            .offset(offset)
            .limit(limit)
        )
        return list((await self.session.scalars(statement)).all())

    async def save(self, task: TaskModel) -> TaskModel:
        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def add_event(
        self, task_id: UUID, event_type: str, message: str | None = None
    ) -> TaskEventModel:
        event = TaskEventModel(task_id=task_id, event_type=event_type, message=message)
        self.session.add(event)
        await self.session.flush()
        await self.session.refresh(event)
        return event

    async def list_events(self, task_id: UUID) -> list[TaskEventModel]:
        statement = (
            select(TaskEventModel)
            .where(TaskEventModel.task_id == task_id)
            .order_by(TaskEventModel.id)
        )
        return list((await self.session.scalars(statement)).all())
