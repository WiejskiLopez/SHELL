"""SQL persistence — session factory and UnitOfWork."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


__all__ = [
    "build_session_factory",
    "dispose_session_factory",
    "get_session",
]


def build_session_factory(url: str) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory for the given database URL.

    Supports both SQLite (sqlite+aiosqlite://...) and
    PostgreSQL (postgresql+asyncpg://...).  The underlying engine is attached
    to the returned factory so it can be disposed by ``dispose_session_factory``.
    """
    engine = create_async_engine(
        url,
        echo=False,
        future=True,
        # SQLite-specific: allow same connection across threads (needed by aiosqlite)
        connect_args={"check_same_thread": False} if "sqlite" in url else {},
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    object.__setattr__(session_factory, "_shell_engine", engine)
    return session_factory


async def dispose_session_factory(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Dispose the engine attached to a session factory created by ``build_session_factory``."""
    engine = getattr(session_factory, "_shell_engine", None)
    if isinstance(engine, AsyncEngine):
        await engine.dispose()


async def get_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """Async generator yielding a single AsyncSession (for use with Depends)."""
    async with session_factory() as session:
        yield session
