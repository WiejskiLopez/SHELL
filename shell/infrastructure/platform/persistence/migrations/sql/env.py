"""Alembic env.py for async SQLAlchemy migrations (SQLite + PostgreSQL)."""

from __future__ import annotations

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parents[6]))

# Register models so they are picked up by Alembic
from shell.infrastructure.definition.persistence.sql.models.graph_definition_embedding import (  # noqa: F401 — rejestracja modelu dla Alembic
    GraphDefinitionEmbeddingModel,
)
from shell.infrastructure.platform.persistence.sql.models import Base
from shell.infrastructure.scheduling.persistence.sql.models.scheduler_definition import (  # noqa: F401 — rejestracja modelu dla Alembic
    SchedulerDefinitionModel,
)
from shell.infrastructure.scheduling.persistence.sql.models.scheduler_execution import (  # noqa: F401 — rejestracja modelu dla Alembic
    SchedulerExecutionModel,
)
from shell.infrastructure.user.persistence.sql.models import (  # noqa: F401 — rejestracja modelu dla Alembic
    UserModel,
    UserSkillModel,
    UserStateModel,
)

# Alembic Config object
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_url() -> str:
    # Allow override via env var (used in CI/docker)
    return os.environ.get("SHELL_DATABASE_URL") or config.get_main_option("sqlalchemy.url") or ""


def run_migrations_offline() -> None:
    url = _get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: object) -> None:
    context.configure(
        connection=connection,  # type: ignore[arg-type]
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    url = _get_url()
    connectable = create_async_engine(url, echo=False, future=True)
    async with connectable.connect() as conn:
        await conn.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
