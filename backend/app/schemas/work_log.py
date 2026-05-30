"""WorkFlow — Pydantic schemas for WorkLog + AI responses."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.work_log import AIConfidence


class LogSubmit(BaseModel):
    log_text: str = Field(min_length=10, max_length=5000)


class LogResponse(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    task_title: str | None = None
    employee_id: uuid.UUID
    employee_name: str | None = None
    log_text: str
    file_name: str | None = None
    ai_confidence: AIConfidence
    ai_feedback: str | None
    ai_verified_at: datetime | None
    submitted_at: datetime

    model_config = {"from_attributes": True}


class LogListResponse(BaseModel):
    logs: list[LogResponse]
    total: int


# ── AI response schemas (Pydantic AI validated) ────────────────────────────────
class LogVerificationResult(BaseModel):
    """Structured output from the AI work-log verification."""
    confidence: AIConfidence
    feedback: str = Field(
        description="One-sentence explanation of the confidence rating"
    )


class ManagerSummaryResponse(BaseModel):
    summary: str
    generated_at: datetime
    task_count: int
    overdue_count: int
