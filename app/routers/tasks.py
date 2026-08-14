from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.schemas.tasks import TaskContinue, TaskCreate, TaskRecord, TaskStatus
from app.services.codex_gateway import StubCodexGateway

router = APIRouter(prefix="/tasks", tags=["tasks"])
_gateway = StubCodexGateway()
_tasks: dict[UUID, TaskRecord] = {}


@router.post("", response_model=TaskRecord)
async def create_task(payload: TaskCreate) -> TaskRecord:
    task = TaskRecord(goal=payload.goal, status=TaskStatus.running)
    _tasks[task.id] = task
    try:
        result = await _gateway.start(payload.goal, payload.workspace)
        task.codex_thread_id = result.thread_id
        task.result = result.final_response
        task.status = TaskStatus.completed
    except Exception as exc:  # pragma: no cover - replaced with structured errors in next milestone
        task.status = TaskStatus.failed
        task.result = str(exc)
    return task


@router.get("/{task_id}", response_model=TaskRecord)
async def get_task(task_id: UUID) -> TaskRecord:
    task = _tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/continue", response_model=TaskRecord)
async def continue_task(task_id: UUID, payload: TaskContinue) -> TaskRecord:
    task = _tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if not task.codex_thread_id:
        raise HTTPException(status_code=409, detail="Task has no Codex thread")

    task.status = TaskStatus.running
    result = await _gateway.resume(task.codex_thread_id, payload.instruction)
    task.codex_thread_id = result.thread_id
    task.result = result.final_response
    task.status = TaskStatus.completed
    return task
