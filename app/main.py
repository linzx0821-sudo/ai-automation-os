from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.db import init_db
from app.routers.tasks import router as tasks_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await init_db()
    yield


app = FastAPI(title="AI Automation OS", version="0.1.0", lifespan=lifespan)
app.include_router(tasks_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {"status": "ok", "codex_backend": settings.codex_backend}
