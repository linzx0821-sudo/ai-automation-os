from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TaskStatus(StrEnum):
    queued = "queued"
    running = "running"
    waiting_approval = "waiting_approval"
    completed = "completed"
    failed = "failed"


class TaskCreate(BaseModel):
    goal: str = Field(min_length=3)
    workspace: str | None = None


class TaskRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    goal: str
    status: TaskStatus = TaskStatus.queued
    codex_thread_id: str | None = None
    result: str | None = None


class TaskContinue(BaseModel):
    instruction: str = Field(min_length=1)
