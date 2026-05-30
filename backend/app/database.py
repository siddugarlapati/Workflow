"""
Aegis — Database Layer
Provides:
  - SQLAlchemy async engine (SQLite with WAL mode)
  - Async session factory
"""
from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.config import settings

# ── SQLAlchemy async engine (SQLite + WAL) ─────────────────────────────────────
engine = create_async_engine(
    settings.database_url,
    echo=settings.is_development,
)

# Activate WAL (Write-Ahead Logging) and Normal synchronous mode for concurrency
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.close()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── DB init ───────────────────────────────────────────────────────────────────
async def init_db() -> None:
    """Create all tables defined in SQLModel metadata (dev/test only)."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def close_db() -> None:
    """Dispose the engine connection pool on shutdown."""
    await engine.dispose()
