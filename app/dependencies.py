from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db import get_session
from app.services.codex_gateway import CodexGateway, build_codex_gateway
from app.services.task_service import TaskService


@lru_cache
def _gateway_singleton() -> CodexGateway:
    return build_codex_gateway(get_settings())


def get_codex_gateway() -> CodexGateway:
    return _gateway_singleton()


async def get_task_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    gateway: Annotated[CodexGateway, Depends(get_codex_gateway)],
) -> TaskService:
    return TaskService(session=session, gateway=gateway)


TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
