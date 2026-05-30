from typing import Any, Optional
import json
import uuid
import structlog
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import CurrentUser, require_manager
from app.core.llm_factory import LLMFactory
from app.repositories.user_repository import UserRepository
from app.schemas.task import TaskCreate, TaskResponse
from app.services.task_service import TaskService

logger = structlog.get_logger()
router = APIRouter(prefix="/api/ai", tags=["ai"])


class ChatbotMessage(BaseModel):
    message: str = Field(min_length=3, max_length=5000)


class ChatbotResponse(BaseModel):
    reply: str
    task: Any = None


@router.post("/chatbot", response_model=ChatbotResponse)
async def chatbot_command(
    data: ChatbotMessage,
    current: CurrentUser = Depends(require_manager),
    session: AsyncSession = Depends(get_db),
) -> ChatbotResponse:
    """
    Manager chatbot: Parses instructions, fuzzy matches team members,
    auto-triages risk levels, and registers tasks in the database.
    """
    logger.info("chatbot.command_received", message=data.message)
    
    # 1. Fetch active company employees to inject in the prompt
    user_repo = UserRepository(session)
    employees = await user_repo.get_active_employees()
    
    if not employees:
        return ChatbotResponse(
            reply="I cannot assign any tasks because there are no active employee accounts registered in the database directory."
        )
        
    employees_list = "\n".join([
        f"- Name: {emp.full_name}, Email: {emp.email}, Department: {emp.department or 'General'}"
        for emp in employees
    ])

    # 2. Query Ollama with JSON output schema to parse fields
    system_prompt = (
        "You are the WorkFlow AI Autonomous Supervisor Agent.\n"
        "Your task is to parse a manager's conversational command and translate it into a structured Task schema.\n"
        "You must choose the best-matching employee from the registered directory based on fuzzy names.\n\n"
        "Registered Employees:\n"
        f"{employees_list}\n\n"
        "Analyze the manager's command and respond ONLY with a valid JSON document in this exact structure:\n"
        "{\n"
        '  "matched_employee_email": "string | null (best matched email)",\n'
        '  "title": "string (professional task title)",\n'
        '  "description": "string (concrete work instructions and scope)",\n'
        '  "priority": "low | medium | high | critical",\n'
        '  "deadline_days": 5 (suggested integer deadline in days, default to 5),\n'
        '  "expected_verification_criteria": "string (proof check guidelines: e.g. verify website links or Excel BoxCount)"\n'
        "}\n\n"
        "Be helpful, precise, and strict about capturing expectations."
    )

    try:
        llm = LLMFactory.get_json_llm()
        # ollama expects system and user roles
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Manager Command: {data.message}"}
        ]
        
        response = await llm.ainvoke(messages)
        parsed = json.loads(response.content)
        logger.info("chatbot.parsed_schema", parsed=parsed)
        
    except Exception as exc:
        logger.warning("chatbot.using_offline_fallback", error=str(exc))
        # Robust offline fallback parser
        msg_lower = data.message.lower()
        matched_email = "employee1@demo.com"
        for emp in employees:
            first_name = emp.full_name.split()[0].lower()
            if first_name in msg_lower:
                matched_email = emp.email
                break

        title = "Conversational Task"
        if "ask" in msg_lower and "to" in msg_lower:
            parts = data.message.split(" to ", 1)
            if len(parts) > 1:
                title = parts[1].split(" and ", 1)[0].capitalize()
        
        parsed = {
            "matched_employee_email": matched_email,
            "title": title,
            "description": data.message,
            "priority": "critical" if "critical" in msg_lower else ("high" if "high" in msg_lower or "urgent" in msg_lower else "medium"),
            "deadline_days": 2 if "urgent" in msg_lower or "critical" in msg_lower else 5,
            "expected_verification_criteria": "verify website contains a secure signup form" if "signup" in msg_lower else "General Compliance Check."
        }

    # 3. Resolve matched employee
    matched_email = parsed.get("matched_employee_email")
    assignee = None
    if matched_email:
        assignee = await user_repo.get_by_email(matched_email)
        
    # Fallback to fuzzy scan if email was wrong or None
    if not assignee and len(employees) > 0:
        assignee = employees[0]  # default fallback

    # 4. Formulate the merged description (storing criteria cleanly)
    raw_desc = parsed.get("description", "No description provided.")
    criteria = parsed.get("expected_verification_criteria", "General Compliance Check.")
    full_desc = f"{raw_desc}\n\n[Expected Verification Criteria]:\n{criteria}"

    # Calculate deadline datetime
    deadline_days = parsed.get("deadline_days", 5)
    try:
        days_int = int(deadline_days)
    except Exception:
        days_int = 5
    deadline_dt = datetime.now(timezone.utc) + timedelta(days=days_int)
    # Set to 5 PM
    deadline_dt = deadline_dt.replace(hour=17, minute=0, second=0, microsecond=0)

    # 5. Create the Task!
    try:
        task_create = TaskCreate(
            title=parsed.get("title", "Conversational Assigned Task"),
            description=full_desc,
            assigned_to=assignee.id,
            priority=parsed.get("priority", "medium").lower(),
            deadline=deadline_dt,
        )
        
        task_service = TaskService(session)
        task_resp = await task_service.create(task_create, manager_id=current.id)
        
        reply = (
            f"⚡ **Task Assigned Automatically!**\n\n"
            f"I have successfully created and assigned the task to **{assignee.full_name}**:\n"
            f"- **Title:** {task_resp.title}\n"
            f"- **Priority:** {task_resp.priority.upper()}\n"
            f"- **Deadline:** {task_resp.deadline.strftime('%Y-%m-%d %H:%M')}\n"
            f"- **AI Verification Scope:** {criteria}\n\n"
            f"I will launch automated Playwright and document verification routines once they submit proof!"
        )
        
        return ChatbotResponse(reply=reply, task=task_resp)
        
    except Exception as exc:
        logger.error("chatbot.task_creation_failed", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Failed to create task: {exc}")

ChatbotResponse.model_rebuild()
