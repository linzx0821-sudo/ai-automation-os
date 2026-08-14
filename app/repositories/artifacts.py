from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact import TaskArtifactModel
from app.services.artifact_indexer import ArtifactSnapshot


class ArtifactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def replace(self, task_id: UUID, snapshots: list[ArtifactSnapshot]) -> list[TaskArtifactModel]:
        await self.session.execute(delete(TaskArtifactModel).where(TaskArtifactModel.task_id == task_id))
        artifacts = [
            TaskArtifactModel(
                task_id=task_id,
                path=snapshot.path,
                media_type=snapshot.media_type,
                size_bytes=snapshot.size_bytes,
                sha256=snapshot.sha256,
            )
            for snapshot in snapshots
        ]
        self.session.add_all(artifacts)
        await self.session.flush()
        return artifacts

    async def list(self, task_id: UUID) -> list[TaskArtifactModel]:
        statement = (
            select(TaskArtifactModel)
            .where(TaskArtifactModel.task_id == task_id)
            .order_by(TaskArtifactModel.path)
        )
        return list((await self.session.scalars(statement)).all())
