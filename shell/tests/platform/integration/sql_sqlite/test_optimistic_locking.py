"""Koncept: optymistyczne blokowanie — kolumna version (Integer) + ConcurrentModificationError.

Reguła: każda wersjonowana tabela (model z ``VersionedMixin``) ma kolumnę ``version``
typu ``sqlalchemy.Integer`` oraz podpięty ``version_id_col``; równoległy zapis do tej
samej wersji zgłasza ``ConcurrentModificationError`` (zamiast cichego last-write-wins).

Poprawnie: wszystkie modele z ``VersionedMixin`` mają Integer version + działający lock;
konflikt wersji jest mapowany na ``ConcurrentModificationError`` przez UoW.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa

from shell.execution_service.domain.execution.aggregates.session_execution.value_objects.project_id_ref import (
    ProjectIdRef,
)
from shell.execution_service.domain.execution.aggregates.session_execution.value_objects.session_id_ref import (
    SessionIdRef,
)
from shell.execution_service.domain.execution.aggregates.workflow.repositories.workflow_repository import (
    WorkflowRepository,
)
from shell.execution_service.domain.execution.aggregates.workflow.value_objects.workflow_id import (
    WorkflowId,
)
from shell.execution_service.domain.execution.aggregates.workflow.workflow import Workflow
from shell.execution_service.infrastructure.execution.persistence.sql.models.base import (
    PERSISTENCE_DELIVERY_MODELS,
)
from shell.execution_service.infrastructure.execution.workflow.persistence.sql.unit_of_work import (
    SqlAlchemyWorkflowUnitOfWork,
)
from shell.platform.domain.exceptions.concurrent_modification_error import (
    ConcurrentModificationError,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.infrastructure.persistence.service_schema_migration import service_metadata

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

_VERSIONED_SERVICES: tuple[tuple[str, str, str], ...] = (
    (
        "shell.definition_service",
        "shell.definition_service.infrastructure.definition.persistence.sql.models.base",
        "DefinitionSqlAlchemyModelBase",
    ),
    (
        "shell.execution_service",
        "shell.execution_service.infrastructure.execution.persistence.sql.models.base",
        "ExecutionSqlAlchemyModelBase",
    ),
    (
        "shell.scheduling_service",
        "shell.scheduling_service.infrastructure.scheduling.persistence.sql.models.base",
        "SchedulingSqlAlchemyModelBase",
    ),
    (
        "shell.session_service",
        "shell.session_service.infrastructure.session.persistence.sql.models.base",
        "SessionSqlAlchemyModelBase",
    ),
    (
        "shell.project_service",
        "shell.project_service.infrastructure.project.persistence.sql.models.base",
        "ProjectSqlAlchemyModelBase",
    ),
    (
        "shell.user_service",
        "shell.user_service.infrastructure.user.persistence.sql.models.base",
        "UserSqlAlchemyModelBase",
    ),
    (
        "shell.ingestion_service",
        "shell.ingestion_service.infrastructure.ingestion.persistence.sql.models.base",
        "IngestionSqlAlchemyModelBase",
    ),
)


def _versioned_tables() -> list[str]:
    """Every table that has a ``version`` column -> table name."""
    tables: list[str] = []
    for pkg, base_module, base_class in _VERSIONED_SERVICES:
        metadata = service_metadata(pkg, base_module, base_class)
        for table in metadata.sorted_tables:
            if "version" in table.c:
                tables.append(f"{pkg.rsplit('.', 1)[1]}/{table.name}")
    return tables


def test_all_versioned_tables_declare_integer_version_column() -> None:
    """Każda tabela z kolumną ``version`` ma ją jako sqlalchemy.Integer."""
    violations: list[str] = []
    for pkg, base_module, base_class in _VERSIONED_SERVICES:
        metadata = service_metadata(pkg, base_module, base_class)
        for table in metadata.sorted_tables:
            if "version" not in table.c:
                continue
            column = table.c["version"]
            if not isinstance(column.type, sa.Integer):
                violations.append(
                    f"{table.name}: version={column.type!r} (oczekiwano sqlalchemy.Integer)"
                )
    assert not violations, (
        "Wersjonowane tabele muszą używać kolumny version typu Integer:\n" + "\n".join(violations)
    )


async def test_optimistic_locking_detects_concurrent_modification(
    session_factory: async_sessionmaker,
) -> None:
    """Równoległa zapis do tej samej wersji workflow -> ConcurrentModificationError."""
    workflow_id = WorkflowId(str(uuid.uuid4()))
    now = CreatedAt.from_datetime(datetime(2024, 1, 1, tzinfo=UTC))

    execution_metadata = service_metadata(
        "shell.execution_service",
        "shell.execution_service.infrastructure.execution.persistence.sql.models.base",
        "ExecutionSqlAlchemyModelBase",
    )

    session = session_factory()
    async with session.begin():
        connection = await session.connection()
        await connection.run_sync(execution_metadata.create_all)
    await session.close()

    workflow = Workflow.create(
        id_=workflow_id,
        now=now,
        session_id=SessionIdRef("session-id"),
        project_id=ProjectIdRef("project-id"),
    )

    uow_a = SqlAlchemyWorkflowUnitOfWork(
        session_factory,
        models=PERSISTENCE_DELIVERY_MODELS,
    )
    uow_b = SqlAlchemyWorkflowUnitOfWork(
        session_factory,
        models=PERSISTENCE_DELIVERY_MODELS,
    )

    async with uow_a as ua:
        await ua.repository(WorkflowRepository).save(workflow)
        await ua.commit()

    session = session_factory()
    async with session.begin():
        result = await session.execute(
            sa.text("SELECT version FROM workflow WHERE id = :id").bindparams(id=workflow_id.value)
        )
        version_after_insert = result.scalar_one()
        assert version_after_insert == 1, "wersja po wstawieniu musi być 1"
    await session.close()

    async with uow_a as ua:
        loaded_a = await ua.repository(WorkflowRepository).get_by_id(workflow_id)
        assert loaded_a is not None
        loaded_a.finish()
        await ua.repository(WorkflowRepository).save(loaded_a)

        async with uow_b as ub:
            loaded_b = await ub.repository(WorkflowRepository).get_by_id(workflow_id)
            assert loaded_b is not None
            loaded_b.abort(reason="concurrent")
            await ub.repository(WorkflowRepository).save(loaded_b)

            await ua.commit()

            session_after = session_factory()
            async with session_after.begin():
                result = await session_after.execute(
                    sa.text("SELECT version FROM workflow WHERE id = :id").bindparams(
                        id=workflow_id.value
                    )
                )
                assert result.scalar_one() == 2, "wersja po commicie ua musi wzrosnąć do 2"
            await session_after.close()

            with pytest.raises(ConcurrentModificationError):
                await ub.commit()
