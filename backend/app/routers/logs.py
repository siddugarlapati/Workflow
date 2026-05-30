"""WorkFlow — Work Logs Router."""
import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import CurrentUser, get_current_user
from app.schemas.work_log import LogListResponse, LogResponse, LogSubmit
from app.services.log_service import LogService

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.post("/{task_id}", response_model=LogResponse, status_code=201)
async def submit_log(
    task_id: uuid.UUID,
    request: Request,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> LogResponse:
    """Employee: submit a daily work log for a task. Triggers AI verification (supports files)."""
    content_type = request.headers.get("content-type", "")
    log_text = ""
    file_bytes = None
    file_name = None

    if "multipart/form-data" in content_type:
        form = await request.form()
        log_text = form.get("log_text", "")
        if not isinstance(log_text, str):
            log_text = ""
        file_field = form.get("file")
        if file_field and hasattr(file_field, "file"):
            file_bytes = await file_field.read()
            file_name = file_field.filename
    else:
        # Fallback to standard JSON parsing (for tests/API compatibility)
        try:
            body = await request.json()
            log_text = body.get("log_text", "")
        except Exception:
            pass

    return await LogService(session).submit(
        task_id=task_id,
        employee_id=current.id,
        log_text=log_text,
        file_bytes=file_bytes,
        file_name=file_name,
    )


@router.get("/task/{task_id}", response_model=LogListResponse)
async def get_task_logs(
    task_id: uuid.UUID,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> LogListResponse:
    """Get all logs for a task (manager or assigned employee)."""
    return await LogService(session).get_task_logs(task_id=task_id)


@router.get("/mine", response_model=LogListResponse)
async def my_logs(
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> LogListResponse:
    """Employee: get my own submitted logs."""
    return await LogService(session).get_my_logs(employee_id=current.id)
