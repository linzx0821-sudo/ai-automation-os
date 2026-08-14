from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TaskStatus(StrEnum):
    queued = "queued"
    running = "running"
    waiting_approval = "waiting_approval"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class ApprovalStatus(StrEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class TaskCreate(BaseModel):
    goal: str = Field(min_length=3)
    workspace: str | None = None


class TaskContinue(BaseModel):
    instruction: str = Field(min_length=1)


class ApprovalAction(BaseModel):
    note: str | None = Field(default=None, max_length=1000)


class TaskEventRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: UUID
    event_type: str
    message: str | None
    created_at: datetime


class TaskRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    goal: str
    workspace: str | None
    status: TaskStatus
    codex_thread_id: str | None
    result: str | None
    error: str | None
    approval_required: bool
    approval_status: ApprovalStatus | None
    pending_instruction: str | None
    created_at: datetime
    updated_at: datetime
