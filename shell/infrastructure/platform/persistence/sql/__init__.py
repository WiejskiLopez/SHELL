"""SQL persistence — session factory and UnitOfWork."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from shell.infrastructure.definition.persistence.sql.models import (
    GraphDefinitionModel
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

__all__ = [
    "build_session_factory",
    "get_session",
    "run_migrations",
    "seed_base_data",
]


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


_ALEMBIC_INI = str(Path(__file__).resolve().parents[4] / "alembic.ini")


async def run_migrations(url: str) -> None:
    """Run all Alembic migrations up to head (used by tests and bootstrap)."""
    import asyncio

    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config(_ALEMBIC_INI)
    alembic_cfg.set_main_option("sqlalchemy.url", url)
    script_location = str(Path(_ALEMBIC_INI).parent / "infrastructure" / "platform" / "persistence" / "migrations" / "sql")
    alembic_cfg.set_main_option("script_location", script_location)
    await asyncio.to_thread(command.upgrade, alembic_cfg, "head")


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

    from shell.infrastructure.definition.persistence.sql.models import GraphNodeDefinitionModel

    session = Session(sync_conn)

    graph_definition_model = session.execute(
        select(GraphDefinitionModel).where(GraphDefinitionModel.name == "base_planner")
    ).scalar_one_or_none()

    if graph_definition_model is None:
        graph_definition_model = GraphDefinitionModel(
            id="base-planner-id",
            name="base_planner",
            purpose="default_planning",
        )
        session.add(graph_definition_model)
        session.flush()

    node_exists = session.execute(
        select(GraphNodeDefinitionModel).where(
            GraphNodeDefinitionModel.graph_definition_id == graph_definition_model.id
        )
    ).scalar_one_or_none()

    if node_exists is None:
        session.add(
            GraphNodeDefinitionModel(
                id="base-planner-node-1",
                graph_definition_id=graph_definition_model.id,
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
