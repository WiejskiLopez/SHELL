"""SQL persistence — session factory and UnitOfWork."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from shell_ddd.infrastructure.persistence.sql.models import TemplateGraphModel

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


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


async def seed_base_data(url: str) -> None:
    engine = create_async_engine(url, echo=False, future=True)

    async with engine.begin() as conn:
        await conn.run_sync(_seed_sync)

    await engine.dispose()


def _seed_sync(sync_conn) -> None:
    from sqlalchemy.orm import Session

    from shell_ddd.infrastructure.persistence.sql.models import TemplateGraphNodeModel

    session = Session(sync_conn)

    template = session.execute(
        select(TemplateGraphModel).where(
            TemplateGraphModel.name == "base_planner"
        )
    ).scalar_one_or_none()

    if template is None:
        template = TemplateGraphModel(
            id="base-planner-id",
            name="base_planner",
            purpose="default_planning",
        )
        session.add(template)
        session.flush()

    node_exists = session.execute(
        select(TemplateGraphNodeModel).where(
            TemplateGraphNodeModel.template_graph_id == template.id
        )
    ).scalar_one_or_none()

    if node_exists is None:
        session.add(
            TemplateGraphNodeModel(
                id="base-planner-node-1",
                template_graph_id=template.id,
                position=0,
                mode="agent",
                role="agent",
                node_type="agent",
                model="",
                command="",
                timeout=0,
                retries=0,
                log_level="INFO",
                max_step=None,
                no_ask_user=False,
                autopilot=False,
                status_initial="",
                extra={},
                script="",
                script_type="",
            )
        )

    session.commit()