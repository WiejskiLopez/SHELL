"""SQL persistence — session factory and UnitOfWork."""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def build_session_factory(url: str) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory for the given database URL.

    Supports both SQLite (sqlite+aiosqlite://...) and
    PostgreSQL (postgresql+asyncpg://...).
    """
    engine = create_async_engine(
        url,
        echo=False,
        future=True,
        # SQLite-specific: allow same connection across threads (needed by aiosqlite)
        connect_args={"check_same_thread": False} if "sqlite" in url else {},
    )
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def create_all_tables(url: str) -> None:
    """Create all tables (dev/test helper — production uses alembic)."""
    from shell_ddd.infrastructure.persistence.sql.models import Base

    engine = create_async_engine(url, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


async def get_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """Async generator yielding a single AsyncSession (for use with Depends)."""
    async with session_factory() as session:
        yield session
