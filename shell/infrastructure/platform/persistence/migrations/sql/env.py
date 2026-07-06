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

# Wszystkie modele używają platform/Base (jeden wspólny metadata).
# Per-BC base.py to Phase 2 stubs — gdy wyciągasz BC jako mikroserwis
# z osobną bazą danych, migrunjesz modele do per-BC Base.
from shell.infrastructure.definition.graph_definition_embedding.persistence.sql.models.graph_definition_embedding import (  # noqa: F401 — rejestracja modeli dla Alembic autogenerate
    GraphDefinitionEmbeddingModel,
)

# Jawna rejestracja modeli per-BC — zapewnia wykrywanie przez Alembic
from shell.infrastructure.definition.persistence.sql.models import (  # noqa: F401 — rejestracja modeli
    GraphDefinitionModel,
    NodeDefinitionModel,
    NodeLinkDefinitionModel,
    RagChunkModel,
    RagDocumentModel,
    RunnerConfigModel,
)
from shell.infrastructure.execution.persistence.sql.models import (  # noqa: F401 — rejestracja modeli
    EdgeExecutionModel,
    EdgeLinkExecutionModel,
    GraphExecutionModel,
    GraphExecutionStateInputModel,
    GraphExecutionStateOutputModel,
    NodeExecutionModel,
    NodeExecutionResultModel,
    NodeExecutionStateModel,
    NodeLinkExecutionModel,
    SessionExecutionModel,
    SessionExecutionStateModel,
    TaskExecutionModel,
    TaskExecutionStateModel,
)
from shell.infrastructure.platform.persistence.sql.models import Base as PlatformBase
from shell.infrastructure.project.persistence.sql.models import (  # noqa: F401 — rejestracja modeli
    ProjectModel,
    ProjectSkillModel,
    ProjectStateModel,
)
from shell.infrastructure.scheduling.scheduler_definition.persistence.sql.models.scheduler_definition import (  # noqa: F401 — rejestracja modeli dla Alembic autogenerate
    SchedulerDefinitionModel,
)
from shell.infrastructure.scheduling.scheduler_execution.persistence.sql.models.scheduler_execution import (  # noqa: F401 — rejestracja modeli dla Alembic autogenerate
    SchedulerExecutionModel,
)
from shell.infrastructure.session.persistence.sql.models import (  # noqa: F401 — rejestracja modeli
    SessionModel,
)
from shell.infrastructure.user.persistence.sql.models import (  # noqa: F401 — rejestracja modeli
    UserModel,
    UserSkillModel,
    UserStateModel,
)

# Alembic Config object
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Jeden metadata — wszystkie tabele są w platform/Base.metadata
target_metadata = PlatformBase.metadata


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
