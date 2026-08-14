from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db import get_session
from app.services.artifact_indexer import ArtifactIndexer
from app.services.codex_gateway import CodexGateway, build_codex_gateway
from app.services.task_service import TaskService


@lru_cache
def _gateway_singleton() -> CodexGateway:
    return build_codex_gateway(get_settings())


def get_codex_gateway() -> CodexGateway:
    return _gateway_singleton()


@lru_cache
def _artifact_indexer_singleton() -> ArtifactIndexer:
    settings = get_settings()
    return ArtifactIndexer(
        root=settings.codex_workspace_root,
        default_workspace=settings.codex_default_workspace,
    )


async def get_task_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    gateway: Annotated[CodexGateway, Depends(get_codex_gateway)],
) -> TaskService:
    return TaskService(
        session=session,
        gateway=gateway,
        artifact_indexer=_artifact_indexer_singleton(),
    )


TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
