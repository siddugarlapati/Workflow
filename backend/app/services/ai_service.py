"""
Aegis — AI Service (Gemini-Powered)
=======================================
All AI inference powered exclusively by Google Gemini 2.5 Flash.
Implements:
  1. verifyLog()               — evaluate work log credibility
  2. generateManagerSummary()  — plain-English team briefing
  3. suggestTaskPriority()     — smart task triage
  4. WorkflowAgent             — LangGraph multi-step accountability agent
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Annotated, Any, TypedDict

import structlog
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.llm_factory import LLMFactory
from app.schemas.work_log import LogVerificationResult
from app.models.work_log import AIConfidence

logger = structlog.get_logger()

# ─────────────────────────────────────────────────────────────────────────────
# Prompts
# ─────────────────────────────────────────────────────────────────────────────

VERIFY_SYSTEM = """\
You are WorkFlow's AI Accountability Supervisor powered by Google Gemini.
Your role is to evaluate whether an employee's daily work log entry genuinely
reflects real progress on their assigned task. Be fair but critically examine
vague, evasive, or off-topic entries. Consider linguistic authenticity,
specificity of outcomes, and alignment with the task description."""

VERIFY_USER = """\
Task title: {title}
Task description: {description}

Employee's work log entry:
{log_text}

Evaluate this log entry. Respond ONLY with valid JSON in this exact format:
{{"confidence": "High" | "Medium" | "Low", "feedback": "one sentence explanation"}}

High = detailed, specific, and clearly relevant — outcomes are verifiable.
Medium = partially relevant or somewhat vague — needs improvement.
Low = vague, off-topic, copy-paste, or looks like bluffing — flag it."""

SUMMARY_SYSTEM = """\
You are WorkFlow's AI team intelligence briefer powered by Google Gemini.
Help the manager understand their team's current work status concisely.
Be direct, highlight risks first, then standouts. Use bold for names."""

SUMMARY_USER = """\
Here is the current task list for the team:
{task_table}

Write a sharp, executive-style briefing (3-5 sentences) covering:
1) Who is overdue or at risk of missing deadlines
2) Who is performing well with verified submissions  
3) Any AI-flagged concerns or patterns to watch
Be specific with names and task titles. Do not list every task — synthesise."""

TRIAGE_SYSTEM = """\
You are WorkFlow's AI task triage engine powered by Google Gemini.
Given a task description, suggest an appropriate priority level and realistic
deadline. Return ONLY valid JSON: {{"priority": "low|medium|high|critical", "deadline_days": <int>, "reasoning": "..."}}"""


# ─────────────────────────────────────────────────────────────────────────────
# 1. Work-Log Verification
# ─────────────────────────────────────────────────────────────────────────────

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)
async def verifyLog(
    task_title: str,
    task_description: str | None,
    log_text: str,
) -> LogVerificationResult:
    """
    Uses Gemini 2.5 Flash to evaluate an employee work log.
    Returns LogVerificationResult(confidence, feedback).
    Retries up to 3× on transient failures with exponential back-off.
    """
    llm = LLMFactory.get_json_llm()
    messages = [
        SystemMessage(content=VERIFY_SYSTEM),
        HumanMessage(
            content=VERIFY_USER.format(
                title=task_title,
                description=task_description or "No description provided.",
                log_text=log_text,
            )
        ),
    ]

    try:
        response = await llm.ainvoke(messages)
        raw = response.content if hasattr(response, "content") else str(response)

        data = _extract_json(raw)
        confidence_str = data.get("confidence", "Medium")
        feedback = data.get("feedback", "Unable to parse AI feedback.")

        confidence_map = {
            "high": AIConfidence.HIGH,
            "medium": AIConfidence.MEDIUM,
            "low": AIConfidence.LOW,
        }
        confidence = confidence_map.get(confidence_str.lower(), AIConfidence.MEDIUM)

        logger.info("ai.verify_log.success", task=task_title, confidence=confidence)
        return LogVerificationResult(confidence=confidence, feedback=feedback)

    except Exception as exc:
        logger.warning("ai.verify_log.failed", error=str(exc))
        return LogVerificationResult(
            confidence=AIConfidence.MEDIUM,
            feedback="Unable to verify — Gemini review pending. Manual oversight recommended.",
        )


# ─────────────────────────────────────────────────────────────────────────────
# 2. Manager Summary ("Where's my team?")
# ─────────────────────────────────────────────────────────────────────────────

@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    reraise=True,
)
async def generateManagerSummary(tasks: list[dict[str, Any]]) -> str:
    """
    Generates a plain-English manager briefing from the task list using Gemini.
    """
    if not tasks:
        return "No tasks are currently assigned. The team has a clean slate — consider assigning new objectives."

    now = datetime.now(timezone.utc)

    rows = []
    for t in tasks:
        deadline = t.get("deadline", "")
        try:
            dl = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
            days_left = (dl - now).days
            deadline_label = f"{deadline[:10]} ({days_left:+d}d)"
        except Exception:
            deadline_label = deadline

        rows.append(
            f"• {t['title']} | {t.get('assignedTo', 'Unassigned')} "
            f"| {t.get('priority', 'medium').upper()} priority "
            f"| deadline {deadline_label} | status: {t.get('status', 'pending')}"
        )

    task_table = "\n".join(rows)

    llm = LLMFactory.get_chat_llm(temperature=0.25)
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(SUMMARY_SYSTEM),
        HumanMessagePromptTemplate.from_template(SUMMARY_USER),
    ])
    chain = prompt | llm | StrOutputParser()

    try:
        summary = await chain.ainvoke({"task_table": task_table})
        logger.info("ai.manager_summary.generated", task_count=len(tasks))
        return summary.strip()
    except Exception as exc:
        logger.warning("ai.manager_summary.failed", error=str(exc))
        return (
            "**AI Summary Unavailable:** Gemini API is temporarily unreachable. "
            "Please check your GEMINI_API_KEY configuration and try again."
        )


# ─────────────────────────────────────────────────────────────────────────────
# 3. Smart Task Triage (priority + deadline suggestion)
# ─────────────────────────────────────────────────────────────────────────────

async def suggestTaskPriority(title: str, description: str) -> dict[str, Any]:
    """
    Given a task title + description, suggest priority and deadline via Gemini.
    Returns: {priority, deadline_days, reasoning}
    """
    llm = LLMFactory.get_json_llm()
    messages = [
        SystemMessage(content=TRIAGE_SYSTEM),
        HumanMessage(content=f"Task: {title}\nDescription: {description}"),
    ]
    try:
        response = await llm.ainvoke(messages)
        raw = response.content if hasattr(response, "content") else str(response)
        return _extract_json(raw)
    except Exception as exc:
        logger.warning("ai.triage.failed", error=str(exc))
        return {"priority": "medium", "deadline_days": 7, "reasoning": "Default suggestion"}


# ─────────────────────────────────────────────────────────────────────────────
# 4. LangGraph Agent — WorkFlow Accountability Agent
# ─────────────────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    """State passed between LangGraph nodes."""
    messages: list[BaseMessage]
    task_context: dict[str, Any]
    analysis: str
    recommendations: list[str]
    risk_level: str  # low | medium | high | critical


def _build_accountability_graph() -> StateGraph:
    """
    LangGraph agent that runs multi-step analysis on a task batch using Gemini.
    Steps: analyse_risks → flag_anomalies → generate_recommendations
    """
    llm = LLMFactory.get_chat_llm(temperature=0.2)

    async def analyse_risks(state: AgentState) -> AgentState:
        tasks = state["task_context"].get("tasks", [])
        overdue = [t for t in tasks if t.get("status") == "overdue"]
        high_priority = [t for t in tasks if t.get("priority") in ("high", "critical")]
        no_logs = [t for t in tasks if t.get("log_count", 0) == 0]

        analysis = (
            f"Gemini Risk Analysis: {len(overdue)} overdue tasks, "
            f"{len(high_priority)} high/critical priority items, "
            f"{len(no_logs)} tasks with zero work log submissions."
        )
        state["analysis"] = analysis
        state["risk_level"] = "critical" if len(overdue) > 3 else ("high" if overdue else "medium")
        return state

    async def flag_anomalies(state: AgentState) -> AgentState:
        tasks = state["task_context"].get("tasks", [])
        low_conf_employees: dict[str, int] = {}
        for t in tasks:
            if t.get("latest_ai_confidence") == "Low":
                emp = t.get("assignedTo", "Unknown")
                low_conf_employees[emp] = low_conf_employees.get(emp, 0) + 1

        anomalies = [
            f"{emp} has {count} tasks flagged as Low confidence"
            for emp, count in low_conf_employees.items()
            if count >= 2
        ]
        if anomalies:
            state["messages"].append(
                AIMessage(content=f"Anomalies detected: {'; '.join(anomalies)}")
            )
        return state

    async def generate_recommendations(state: AgentState) -> AgentState:
        context = (
            f"Current situation: {state['analysis']}\n"
            f"Risk level: {state['risk_level']}\n"
            f"Anomalies: {[m.content for m in state['messages'] if isinstance(m, AIMessage)]}"
        )
        messages = [
            SystemMessage(
                content="You are WorkFlow's AI productivity coach powered by Gemini. "
                        "Give 3 specific, concise, actionable recommendations."
            ),
            HumanMessage(content=context),
        ]
        response = await llm.ainvoke(messages)
        recs = [
            line.strip()
            for line in response.content.split("\n")
            if line.strip() and line[0].isdigit()
        ]
        state["recommendations"] = recs[:3] if recs else ["Review overdue tasks and schedule 1:1 check-ins immediately."]
        return state

    graph = StateGraph(AgentState)
    graph.add_node("analyse_risks", analyse_risks)
    graph.add_node("flag_anomalies", flag_anomalies)
    graph.add_node("generate_recommendations", generate_recommendations)
    graph.add_edge(START, "analyse_risks")
    graph.add_edge("analyse_risks", "flag_anomalies")
    graph.add_edge("flag_anomalies", "generate_recommendations")
    graph.add_edge("generate_recommendations", END)

    return graph.compile()


_accountability_agent = _build_accountability_graph()


async def runAccountabilityAgent(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Runs the LangGraph accountability agent on the full task list via Gemini.
    Returns: {analysis, risk_level, recommendations}
    """
    initial_state: AgentState = {
        "messages": [],
        "task_context": {"tasks": tasks},
        "analysis": "",
        "recommendations": [],
        "risk_level": "low",
    }
    final_state = await _accountability_agent.ainvoke(initial_state)
    return {
        "analysis": final_state["analysis"],
        "risk_level": final_state["risk_level"],
        "recommendations": final_state["recommendations"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5. RAG Service — No-Op Stub (SQLite environment, no vector DB needed)
# ─────────────────────────────────────────────────────────────────────────────

class RAGService:
    """
    Semantic search stub. Gemini's context window handles in-context retrieval.
    For production pgvector deployments, replace with Gemini embedding API.
    """
    _index: Any = None

    @classmethod
    async def initialize(cls, database_url: str) -> None:
        logger.info("rag.initialized", mode="gemini_context_window", database=database_url[:30])

    @classmethod
    async def search_similar_logs(
        cls,
        query: str,
        task_id: uuid.UUID | None = None,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        return []

    @classmethod
    async def index_log(cls, log_text: str, metadata: dict[str, Any]) -> None:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────────────────────

def _extract_json(raw: str) -> dict[str, Any]:
    """Robustly extract JSON from Gemini output."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    match = re.search(r"\{.*?\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Cannot extract JSON from Gemini output: {raw[:200]}")
