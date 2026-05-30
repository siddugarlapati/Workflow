"""
Aegis — FastAPI Application Factory
=======================================
Registers all routers, middleware, lifespan events, and CORS.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
import asyncio
from app.database import close_db, init_db, AsyncSessionLocal
from app.routers import ai, audit, auth, logs, tasks, chatbot
from app.services.ai_service import RAGService
from app.services.task_service import TaskService

logger = structlog.get_logger()


async def overdue_checker_daemon() -> None:
    """Asynchronous cron daemon periodically verifying and marking overdue tasks."""
    logger.info("daemon.overdue_checker.started")
    while True:
        try:
            async with AsyncSessionLocal() as session:
                service = TaskService(session)
                marked_count = await service.mark_overdue_tasks()
                if marked_count > 0:
                    logger.info("daemon.overdue_checker.marked_tasks", count=marked_count)
                await session.commit()
        except Exception as exc:
            logger.error("daemon.overdue_checker.error", error=str(exc))
        
        await asyncio.sleep(60)  # Verify every 60 seconds


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown lifecycle management."""
    # ── Startup ───────────────────────────────────────────────────────────────
    logger.info("workflow.startup", env=settings.app_env)

    # Spawn real-time overdue checker background daemon
    daemon_task = asyncio.create_task(overdue_checker_daemon())

    # Init DB tables (dev/test)
    if settings.is_development:
        await init_db()
        logger.info("db.tables_created")

    # Init RAG vector index
    await RAGService.initialize(database_url=settings.database_url.replace(
        "postgresql+asyncpg://", "postgresql://"
    ))

    logger.info("workflow.ready", host=settings.app_host, port=settings.app_port)
    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    daemon_task.cancel()
    try:
        await daemon_task
    except asyncio.CancelledError:
        pass
    await close_db()
    logger.info("workflow.shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Aegis API",
        description=(
            "AI-Powered, Role-Based Employee Task & Accountability Platform. "
            "Built with FastAPI + LangChain + LangGraph + Gemini 2.5 Flash."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins in development
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(auth.router)
    app.include_router(tasks.router)
    app.include_router(logs.router)
    app.include_router(ai.router)
    app.include_router(audit.router)
    app.include_router(chatbot.router)

    # ── Health & Root ─────────────────────────────────────────────────────────
    @app.get("/", tags=["root"])
    async def root() -> dict:
        return {
            "app": "Aegis",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs",
        }

    @app.get("/health", tags=["root"])
    async def health() -> dict:
        return {"status": "healthy", "env": settings.app_env}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
