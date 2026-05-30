"""
WorkFlow — WorkLog Model
Stores employee daily work logs with AI confidence scores.
"""
import uuid
from datetime import datetime
from enum import StrEnum
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class AIConfidence(StrEnum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    PENDING = "Pending"  # Before AI verification runs


class WorkLog(SQLModel, table=True):
    __tablename__ = "work_logs"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )
    task_id: uuid.UUID = Field(foreign_key="tasks.id", index=True)
    employee_id: uuid.UUID = Field(foreign_key="profiles.id", index=True)
    log_text: str  # The free-text work log entry
    file_name: Optional[str] = Field(default=None)
    ai_confidence: AIConfidence = Field(default=AIConfidence.PENDING)
    ai_feedback: Optional[str] = Field(default=None)  # One-sentence AI explanation
    ai_verified_at: Optional[datetime] = Field(default=None)
    submitted_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    task: "Task" = Relationship(back_populates="work_logs")  # type: ignore[name-defined]  # noqa: F821
    employee: "User" = Relationship(back_populates="work_logs")  # type: ignore[name-defined]  # noqa: F821
