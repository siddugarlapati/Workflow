"""WorkFlow — Work Log Service."""
import uuid
from datetime import datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.work_log import WorkLog
from app.repositories.audit_repository import AuditRepository
from app.repositories.log_repository import LogRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.work_log import LogListResponse, LogResponse, LogSubmit
from app.services.ai_service import RAGService, verifyLog

logger = structlog.get_logger()


from app.core.document_parser import extract_text_from_document


def _log_to_response(log: WorkLog) -> LogResponse:
    return LogResponse(
        id=log.id,
        task_id=log.task_id,
        task_title=log.task.title if log.task else None,
        employee_id=log.employee_id,
        employee_name=log.employee.full_name if log.employee else None,
        log_text=log.log_text,
        file_name=log.file_name,
        ai_confidence=log.ai_confidence,
        ai_feedback=log.ai_feedback,
        ai_verified_at=log.ai_verified_at,
        submitted_at=log.submitted_at,
    )


class LogService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = LogRepository(session)
        self.task_repo = TaskRepository(session)
        self.audit = AuditRepository(session)

    async def submit(
        self,
        task_id: uuid.UUID,
        employee_id: uuid.UUID,
        log_text: str,
        file_bytes: bytes | None = None,
        file_name: str | None = None,
    ) -> LogResponse:
        # Verify task exists and belongs to this employee
        task = await self.task_repo.get_by_id_with_relations(task_id)
        if not task:
            raise NotFoundException("Task not found")
        if task.assigned_to != employee_id:
            raise ForbiddenException("You can only log work on your own tasks")

        # ── Parse document if uploaded ────────────────────────────────────────
        full_text = log_text
        if file_bytes and file_name:
            try:
                extracted_text = extract_text_from_document(file_bytes, file_name)
                # Combine employee note and extracted document proof
                if log_text.strip():
                    full_text = f"Employee Notes: {log_text}\n\n[Extracted Document Proof ({file_name})]:\n{extracted_text}"
                else:
                    full_text = f"[Extracted Document Proof ({file_name})]:\n{extracted_text}"
            except Exception as exc:
                logger.error("log.submit.document_parse_failed", error=str(exc))
                raise ValueError(f"Could not parse uploaded document: {exc}")

        # Check for empty logs
        if not full_text or not full_text.strip():
            raise ValueError("Either a text log or a document proof must be provided")

        # Create the log entry
        log = WorkLog(
            task_id=task_id,
            employee_id=employee_id,
            log_text=full_text,
            file_name=file_name,
        )
        log = await self.repo.create(log)

        # ── AI Verification (inline, fast enough for 3b model) ───────────────
        try:
            # Extract criteria if saved by chatbot
            expected_criteria = None
            if task.description and "[Expected Verification Criteria]:" in task.description:
                parts = task.description.split("[Expected Verification Criteria]:")
                expected_criteria = parts[1].strip()

            from app.core.automated_verifier import run_cognitive_verification
            result = await run_cognitive_verification(
                task_title=task.title,
                task_desc=task.description,
                log_text=full_text,
                expected_criteria=expected_criteria
            )
            log.ai_confidence = result.confidence
            log.ai_feedback = result.feedback
            log.ai_verified_at = datetime.utcnow()
            await self.repo.update(log, {
                "ai_confidence": result.confidence,
                "ai_feedback": result.feedback,
                "ai_verified_at": log.ai_verified_at,
            })
            logger.info("log.ai_verified", log_id=str(log.id), confidence=result.confidence)
        except Exception as exc:
            logger.warning("log.ai_verify_error", error=str(exc))

        # ── Index in RAG ──────────────────────────────────────────────────────
        await RAGService.index_log(
            log_text=full_text,
            metadata={
                "log_id": str(log.id),
                "task_id": str(task_id),
                "task_title": task.title,
                "employee_id": str(employee_id),
                "file_name": file_name,
            },
        )

        # ── Audit ─────────────────────────────────────────────────────────────
        await self.audit.log_action(
            actor_id=employee_id,
            action="log_submitted",
            entity_type="work_log",
            entity_id=log.id,
            payload={
                "task_id": str(task_id),
                "ai_confidence": log.ai_confidence,
                "file_name": file_name,
                "log_preview": full_text[:100],
            },
        )

        # Reload with relations for full response
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        from app.models.work_log import WorkLog as WLModel
        stmt = (
            select(WLModel)
            .where(WLModel.id == log.id)
            .options(selectinload(WLModel.task), selectinload(WLModel.employee))
        )
        result2 = await self.repo.session.execute(stmt)
        log = result2.scalar_one()
        return _log_to_response(log)

    async def get_task_logs(self, task_id: uuid.UUID) -> LogListResponse:
        logs = await self.repo.get_by_task(task_id)
        return LogListResponse(
            logs=[_log_to_response(lg) for lg in logs],
            total=len(logs),
        )

    async def get_my_logs(self, employee_id: uuid.UUID) -> LogListResponse:
        logs = await self.repo.get_by_employee(employee_id)
        return LogListResponse(
            logs=[_log_to_response(lg) for lg in logs],
            total=len(logs),
        )
