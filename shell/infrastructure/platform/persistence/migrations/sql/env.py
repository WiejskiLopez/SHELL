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
# Każdy agregat rejestruje swój model samodzielnie — brak centralnego re-eksportu.
# Jawna rejestracja modeli per-BC — zapewnia wykrywanie przez Alembic
from shell.infrastructure.definition.graph_definition.persistence.sql.models import (  # noqa: F401 — rejestracja modeli
    GraphDefinitionModel,
)
from shell.infrastructure.definition.graph_definition_embedding.persistence.sql.models.graph_definition_embedding import (  # noqa: F401 — rejestracja modeli
    GraphDefinitionEmbeddingModel,
)
from shell.infrastructure.definition.node_definition.persistence.sql.models import (  # noqa: F401 — rejestracja modeli
    NodeDefinitionModel,
)
from shell.infrastructure.definition.node_link_definition.persistence.sql.models import (  # noqa: F401 — rejestracja modeli
    NodeLinkDefinitionModel,
)
from shell.infrastructure.definition.rag_document.persistence.sql.models import (  # noqa: F401 — rejestracja modeli
    RagChunkModel,
    RagDocumentModel,
)
from shell.infrastructure.definition.runner_config.persistence.sql.models import (  # noqa: F401 — rejestracja modeli
    RunnerConfigModel,
)

# --- Execution BC (każdy agregat osobno) ---
from shell.infrastructure.execution.edge_execution.persistence.sql.models import (
    EdgeExecutionModel,  # noqa: F401 — Alembic autogenerate
)
from shell.infrastructure.execution.edge_link_execution.persistence.sql.models import (
    EdgeLinkExecutionModel,  # noqa: F401 — Alembic autogenerate
)
from shell.infrastructure.execution.graph_execution.persistence.sql.models import (
    GraphExecutionModel,  # noqa: F401 — Alembic autogenerate
)
from shell.infrastructure.execution.graph_execution_state.persistence.sql.models import (  # noqa: F401 — Alembic autogenerate
    GraphExecutionStateInputModel,
    GraphExecutionStateOutputModel,
)
from shell.infrastructure.execution.node_execution.persistence.sql.models import (  # noqa: F401 — Alembic autogenerate
    NodeExecutionModel,
    NodeExecutionResultModel,
)
from shell.infrastructure.execution.node_execution_state.persistence.sql.models import (
    NodeExecutionStateModel,  # noqa: F401 — Alembic autogenerate
)
from shell.infrastructure.execution.node_link_execution.persistence.sql.models import (
    NodeLinkExecutionModel,  # noqa: F401 — Alembic autogenerate
)
from shell.infrastructure.execution.session_execution.persistence.sql.models import (
    SessionExecutionModel,  # noqa: F401 — Alembic autogenerate
)
from shell.infrastructure.execution.session_execution_state.persistence.sql.models import (
    SessionExecutionStateModel,  # noqa: F401 — Alembic autogenerate
)
from shell.infrastructure.execution.task_execution.persistence.sql.models import (
    TaskExecutionModel,  # noqa: F401 — Alembic autogenerate
)
from shell.infrastructure.execution.task_execution_state.persistence.sql.models import (
    TaskExecutionStateModel,  # noqa: F401 — Alembic autogenerate
)
from shell.infrastructure.platform.persistence.sql.models import Base as PlatformBase
from shell.infrastructure.project.project.persistence.sql.models.project import (  # noqa: F401 — rejestracja modeli
    ProjectModel,
)
from shell.infrastructure.project.project_skill.persistence.sql.models.project_skill import (  # noqa: F401 — rejestracja modeli
    ProjectSkillModel,
)
from shell.infrastructure.project.project_state.persistence.sql.models.project_state import (  # noqa: F401 — rejestracja modeli
    ProjectStateModel,
)
from shell.infrastructure.scheduling.scheduler_definition.persistence.sql.models.scheduler_definition import (  # noqa: F401 — rejestracja modeli dla Alembic autogenerate
    SchedulerDefinitionModel,
)
from shell.infrastructure.scheduling.scheduler_execution.persistence.sql.models.scheduler_execution import (  # noqa: F401 — rejestracja modeli dla Alembic autogenerate
    SchedulerExecutionModel,
)
from shell.infrastructure.session.session.persistence.sql.models.session import (  # noqa: F401 — rejestracja modeli
    SessionModel,
)
from shell.infrastructure.user.user.persistence.sql.models.user import (  # noqa: F401 — rejestracja modeli
    UserModel,
)
from shell.infrastructure.user.user_skill.persistence.sql.models.user_skill import (  # noqa: F401 — rejestracja modeli
    UserSkillModel,
)
from shell.infrastructure.user.user_state.persistence.sql.models.user_state import (  # noqa: F401 — rejestracja modeli
    UserStateModel,
)

# Alembic Config object
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Jeden metadata — wszystkie tabele są w platform/Base.metadata
target_metadata = PlatformBase.metadata


def include_object(obj: object, name: str, type_: str, reflected: bool, compare_to: object) -> bool:
    """Nie generuj DROP TABLE dla tabel nieobecnych w metadata.

    Daje pełną kontrolę nad zmianami schematu — tylko jawne migracje
    mogą usuwać tabele.
    """
    return not (type_ == "table" and reflected and not compare_to)


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
        include_object=include_object,  # type: ignore[arg-type]
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: object) -> None:
    context.configure(
        connection=connection,  # type: ignore[arg-type]
        target_metadata=target_metadata,
        compare_type=True,
        include_object=include_object,  # type: ignore[arg-type]
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
