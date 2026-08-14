from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.dependencies import TaskServiceDep
from app.schemas.tasks import (
    ApprovalAction,
    TaskContinue,
    TaskCreate,
    TaskEventRecord,
    TaskRecord,
)
from app.services.task_service import TaskConflictError, TaskNotFoundError

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskRecord)
async def create_task(payload: TaskCreate, service: TaskServiceDep) -> TaskRecord:
    task = await service.create_and_run(goal=payload.goal, workspace=payload.workspace)
    return TaskRecord.model_validate(task)


@router.get("/{task_id}", response_model=TaskRecord)
async def get_task(task_id: UUID, service: TaskServiceDep) -> TaskRecord:
    try:
        task = await service.get(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc
    return TaskRecord.model_validate(task)


@router.get("/{task_id}/events", response_model=list[TaskEventRecord])
async def get_task_events(task_id: UUID, service: TaskServiceDep) -> list[TaskEventRecord]:
    try:
        events = await service.events(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc
    return [TaskEventRecord.model_validate(event) for event in events]


@router.post("/{task_id}/continue", response_model=TaskRecord)
async def continue_task(
    task_id: UUID,
    payload: TaskContinue,
    service: TaskServiceDep,
) -> TaskRecord:
    try:
        task = await service.continue_and_run(task_id, payload.instruction)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc
    except TaskConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return TaskRecord.model_validate(task)


@router.post("/{task_id}/approve", response_model=TaskRecord)
async def approve_task(
    task_id: UUID,
    payload: ApprovalAction,
    service: TaskServiceDep,
) -> TaskRecord:
    try:
        task = await service.approve(task_id, payload.note)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc
    except TaskConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return TaskRecord.model_validate(task)


@router.post("/{task_id}/reject", response_model=TaskRecord)
async def reject_task(
    task_id: UUID,
    payload: ApprovalAction,
    service: TaskServiceDep,
) -> TaskRecord:
    try:
        task = await service.reject(task_id, payload.note)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc
    except TaskConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return TaskRecord.model_validate(task)
