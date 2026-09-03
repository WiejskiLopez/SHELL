"""Offline pilot test sagi project_provision w project_service.

Drives the real platform pipeline (CommandInboxProcessor, CommandDeliveryDispatcher,
SqlSagaRepository, SagaManager, EventBus) against SQLite. Transport jest
symulowany: wiersze ``outbox_command`` są klonowane do ``inbox_command``
(odpowiednik relay + broker + consumer). Brak brokera w teście.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import MetaData, select
from sqlalchemy.orm import DeclarativeBase

from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.event_bus import EventBus
from shell.platform.application.bus.event_bus_publisher import EventBusPublisher
from shell.platform.application.contracts.command_contract import CommandContract
from shell.platform.infrastructure.messaging.command.processor.command_inbox_processor import (
    CommandInboxProcessor,
)
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.platform.infrastructure.persistence.sql.models.persistence_delivery import (
    build_persistence_delivery_models,
)
from shell.platform.infrastructure.process.saga import build_command_delivery_dispatcher
from shell.platform.infrastructure.process.saga.repositories.sql_saga_repository import (
    SqlSagaRepository,
)
from shell.platform.infrastructure.process.saga.repositories.sql_saga_timeout_repository import (
    SqlSagaTimeoutRepository,
)
from shell.platform.process.saga.base.saga_state import SagaStatus
from shell.project_service.application.project.project_provision.command_handlers.provision_workspace_handler import (
    ProvisionWorkspaceHandler,
)
from shell.project_service.application.project.project_provision.command_handlers.release_workspace_handler import (
    ReleaseWorkspaceHandler,
)
from shell.project_service.application.project.project_provision.commands.provision_workspace_command import (
    ProvisionWorkspaceCommand,
)
from shell.project_service.application.project.project_provision.commands.release_workspace_command import (
    ReleaseWorkspaceCommand,
)
from shell.project_service.application.project.project_provision.commands.start_project_provision_command import (
    StartProjectProvisionCommand,
)
from shell.project_service.application.project.project_provision.integration_events.workspace_provision_failed_integration_event import (
    WorkspaceProvisionFailedIntegrationEvent,
)
from shell.project_service.application.project.project_provision.integration_events.workspace_provisioned_integration_event import (
    WorkspaceProvisionedIntegrationEvent,
)
from shell.project_service.application.project.project_provision.integration_events.workspace_released_integration_event import (
    WorkspaceReleasedIntegrationEvent,
)
from shell.project_service.process.project.project_provision.handlers.start_project_provision_handler import (
    StartProjectProvisionHandler,
)
from shell.project_service.process.project.project_provision.handlers.workspace_provision_failed_handler import (
    WorkspaceProvisionFailedSagaHandler,
)
from shell.project_service.process.project.project_provision.handlers.workspace_provisioned_handler import (
    WorkspaceProvisionedSagaHandler,
)
from shell.project_service.process.project.project_provision.handlers.workspace_released_handler import (
    WorkspaceReleasedSagaHandler,
)
from shell.project_service.process.project.project_provision.manager import (
    build_project_provision_manager_factory,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

SAGA_TYPE = "project_provision"
_SERVICE = "project"


class _PilotTestBase(DeclarativeBase):
    metadata = MetaData()


PERSISTENCE_MODELS = build_persistence_delivery_models(_PilotTestBase)
COMMAND_MODELS = PERSISTENCE_MODELS.commands
SAGA_MODELS = PERSISTENCE_MODELS.sagas

_COMMAND_CLASSES = (
    StartProjectProvisionCommand,
    ProvisionWorkspaceCommand,
    ReleaseWorkspaceCommand,
)

_CONTRACTS: dict[str, CommandContract] = {
    command.__name__: CommandContract(
        command_name=command.__name__,
        command_class=command,
        target_service=_SERVICE,
        schema_version=1,
    )
    for command in _COMMAND_CLASSES
}


@pytest.fixture
async def session_factory(tmp_path) -> async_sessionmaker:
    url = f"sqlite+aiosqlite:///{tmp_path / 'saga.db'}"
    engine = _build_engine(url)
    async with engine.begin() as connection:
        await connection.run_sync(_PilotTestBase.metadata.create_all)
    await engine.dispose()
    return build_session_factory(url)


@pytest.fixture
def flow(session_factory):
    command_bus = CommandBus()
    event_bus = EventBus()
    event_publisher = EventBusPublisher(event_bus)
    dispatcher = build_command_delivery_dispatcher(
        commands=_CONTRACTS,
        models=COMMAND_MODELS,
        source_service=_SERVICE,
    )
    saga_repository = SqlSagaRepository(session_factory, SAGA_MODELS)
    timeout_repository = SqlSagaTimeoutRepository(
        session_factory, SAGA_MODELS, source_service=_SERVICE
    )
    manager_factory = build_project_provision_manager_factory(
        repository=saga_repository,
        dispatcher=dispatcher,
        timeouts=timeout_repository,
    )
    command_bus.register(
        StartProjectProvisionCommand,
        lambda: StartProjectProvisionHandler(manager_factory, saga_repository),
    )
    command_bus.register(
        ProvisionWorkspaceCommand, lambda: ProvisionWorkspaceHandler(event_publisher)
    )
    command_bus.register(ReleaseWorkspaceCommand, lambda: ReleaseWorkspaceHandler(event_publisher))
    event_bus.subscribe(
        WorkspaceProvisionedIntegrationEvent,
        lambda: WorkspaceProvisionedSagaHandler(manager_factory, saga_repository),
    )
    event_bus.subscribe(
        WorkspaceProvisionFailedIntegrationEvent,
        lambda: WorkspaceProvisionFailedSagaHandler(manager_factory, saga_repository),
    )
    event_bus.subscribe(
        WorkspaceReleasedIntegrationEvent,
        lambda: WorkspaceReleasedSagaHandler(manager_factory, saga_repository),
    )
    processor = CommandInboxProcessor(
        session_factory,
        command_bus,
        registry={command.__name__: command for command in _COMMAND_CLASSES},
        models=COMMAND_MODELS,
        max_retries=2,
        retry_backoff_seconds=0,
    )
    return {
        "session_factory": session_factory,
        "processor": processor,
        "saga_repository": saga_repository,
        "command_bus": command_bus,
        "event_bus": event_bus,
    }


def _build_engine(url: str):
    from sqlalchemy.ext.asyncio import create_async_engine

    return create_async_engine(url)


async def _insert_inbox(
    session_factory,
    *,
    command,
    outbox_id: str,
) -> None:
    now = datetime.now(tz=UTC)
    payload = {"project_id": command.project_id, "command_id": f"cmd-{outbox_id}"}
    if getattr(command, "fail", False):
        payload["fail"] = True
    async with session_factory() as session:
        session.add(
            COMMAND_MODELS.inbox(
                id=str(uuid.uuid4()),
                outbox_id=outbox_id,
                command_id=outbox_id,
                command_name=type(command).__name__,
                source_service=_SERVICE,
                target_service=_SERVICE,
                schema_version=1,
                issued_at=now,
                payload=payload,
                correlation_id="corr-" + outbox_id,
                causation_id="caus-orig",
                received_at=now,
            )
        )
        await session.commit()


async def _relay_pending_commands(session_factory) -> int:
    async with session_factory() as session:
        rows = (await session.execute(select(COMMAND_MODELS.outbox))).scalars().all()
        pending = [row for row in rows if row.published_at is None]
    for row in pending:
        now = datetime.now(tz=UTC)
        async with session_factory() as session:
            session.add(
                COMMAND_MODELS.inbox(
                    id=str(uuid.uuid4()),
                    outbox_id=row.id,
                    command_id=row.command_id,
                    command_name=row.command_name,
                    source_service=row.source_service,
                    target_service=row.target_service,
                    schema_version=row.schema_version,
                    issued_at=row.issued_at,
                    payload=dict(row.payload or {}),
                    correlation_id=row.correlation_id,
                    causation_id=row.causation_id,
                    received_at=now,
                )
            )
            await session.commit()
    return len(pending)


async def _pending_outbox_names(session_factory) -> list[str]:
    async with session_factory() as session:
        rows = (await session.execute(select(COMMAND_MODELS.outbox))).scalars().all()
        return [row.command_name for row in rows if row.published_at is None]


class TestProjectProvisionSaga:
    async def test_success_path_completes(self, flow) -> None:
        session_factory = flow["session_factory"]
        processor = flow["processor"]
        saga_repository = flow["saga_repository"]

        await _insert_inbox(
            session_factory,
            command=StartProjectProvisionCommand(project_id="p-1"),
            outbox_id="start-1",
        )
        result = await processor.run_once()
        assert result.processed_count == 1

        assert "ProvisionWorkspaceCommand" in await _pending_outbox_names(session_factory)

        await _relay_pending_commands(session_factory)
        result = await processor.run_once()
        assert result.processed_count == 1

        instance = await saga_repository.get_by_key(SAGA_TYPE, "p-1")
        assert instance is not None
        assert instance.status is SagaStatus.COMPLETED
        assert instance.completed_steps == ("provision_workspace",)
        assert instance.version == 2

    async def test_failure_path_dispatches_compensation(self, flow) -> None:
        session_factory = flow["session_factory"]
        processor = flow["processor"]
        saga_repository = flow["saga_repository"]

        await _insert_inbox(
            session_factory,
            command=StartProjectProvisionCommand(project_id="p-fail", fail=True),
            outbox_id="start-fail",
        )
        result = await processor.run_once()
        assert result.processed_count == 1

        await _relay_pending_commands(session_factory)
        result = await processor.run_once()
        assert result.processed_count == 1

        instance = await saga_repository.get_by_key(SAGA_TYPE, "p-fail")
        assert instance is not None
        assert instance.status is SagaStatus.COMPENSATING
        assert instance.current_step == "compensation:provision_workspace"
        assert instance.failed_steps == ("provision_workspace",)
        names = await _pending_outbox_names(session_factory)
        assert "ReleaseWorkspaceCommand" in names

        await flow["event_bus"].publish(
            [
                WorkspaceReleasedIntegrationEvent(
                    event_id=str(uuid.uuid4()),
                    correlation_id="corr-release",
                    causation_id="caus-release",
                    occurred_at=datetime.now(tz=UTC),
                    aggregate_id="p-fail",
                    schema_version=1,
                    project_id="p-fail",
                )
            ]
        )
        instance = await saga_repository.get_by_key(SAGA_TYPE, "p-fail")
        assert instance is not None
        assert instance.status is SagaStatus.COMPENSATED
        assert instance.current_step is None
