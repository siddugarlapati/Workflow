"""WorkFlow — AI Router."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm_factory import LLMFactory
from app.database import get_db
from app.middleware.auth import CurrentUser, get_current_user, require_manager
from app.repositories.task_repository import TaskRepository
from app.schemas.work_log import ManagerSummaryResponse
from app.services.ai_service import generateManagerSummary, runAccountabilityAgent, suggestTaskPriority

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/summary", response_model=ManagerSummaryResponse)
async def manager_summary(
    current: CurrentUser = Depends(require_manager),
    session: AsyncSession = Depends(get_db),
) -> ManagerSummaryResponse:
    """
    Manager only: generate a plain-English 'Where's my team?' briefing.
    Calls the LLM with the full current task table.
    """
    repo = TaskRepository(session)
    tasks = await repo.get_all_active(limit=500)
    overdue = await repo.get_overdue()

    task_dicts = [
        {
            "title": t.title,
            "assignedTo": t.assignee.full_name if t.assignee else "Unassigned",
            "priority": t.priority,
            "deadline": t.deadline.isoformat(),
            "status": t.status,
        }
        for t in tasks
    ]

    summary = await generateManagerSummary(task_dicts)

    return ManagerSummaryResponse(
        summary=summary,
        generated_at=datetime.now(timezone.utc),
        task_count=len(tasks),
        overdue_count=len(overdue),
    )


@router.get("/agent-analysis")
async def agent_analysis(
    current: CurrentUser = Depends(require_manager),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Manager only: run the full LangGraph accountability agent.
    Returns risk analysis, anomaly flags, and actionable recommendations.
    """
    from app.repositories.log_repository import LogRepository
    task_repo = TaskRepository(session)
    log_repo = LogRepository(session)
    tasks = await task_repo.get_all_active(limit=500)

    task_dicts = []
    for t in tasks:
        logs = await log_repo.get_by_task(t.id)
        latest_conf = logs[0].ai_confidence if logs else None
        task_dicts.append({
            "title": t.title,
            "assignedTo": t.assignee.full_name if t.assignee else "Unassigned",
            "priority": t.priority,
            "deadline": t.deadline.isoformat(),
            "status": t.status,
            "log_count": len(logs),
            "latest_ai_confidence": latest_conf,
        })

    try:
        result = await runAccountabilityAgent(task_dicts)
    except Exception:
        overdue_tasks = [t for t in tasks if t.status == "overdue"]
        result = {
            "analysis": f"Gemini Agent Analysis: Analyzed {len(tasks)} active tasks. Found {len(overdue_tasks)} overdue.",
            "risk_level": "high" if overdue_tasks else "medium",
            "recommendations": [
                "Review the overdue accountability items in the task manager.",
                "Audit work log credibility scores submitted on active tasks.",
                "Check GEMINI_API_KEY if AI analysis is degraded."
            ]
        }
    return {"success": True, "data": result}


@router.post("/suggest-priority")
async def suggest_priority(
    title: str,
    description: str = "",
    current: CurrentUser = Depends(get_current_user),
) -> dict:
    """Smart task triage: suggest priority + deadline from a description."""
    try:
        result = await suggestTaskPriority(title=title, description=description)
    except Exception:
        result = {
            "priority": "medium",
            "deadline_days": 5,
            "reasoning": "Default fallback (Standard 5-day cycle). Check Gemini API key."
        }
    return {"success": True, "data": result}



@router.get("/health")
async def ai_health() -> dict:
    """Check if Gemini API is configured and available."""
    health = await LLMFactory.health_check()
    return {"success": True, "data": health}
