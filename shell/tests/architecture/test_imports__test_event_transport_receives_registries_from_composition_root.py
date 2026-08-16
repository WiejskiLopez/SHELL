"""Koncept: wiring event transportu w standalone service.

Reguła: każdy service musi budować własne registry, a każdy konsument eventów
musi przekazać je do procesora wraz z własnymi modelami delivery.

Poprawnie: composition root tworzy procesor z registry i modelami tego samego
bounded contextu; User pozostaje publisher-only.
"""

from __future__ import annotations

from typing import Any, cast

from shell.definition_service.bootstrap.definition.container.definition_core_container import (
    DefinitionCoreContainer,
)
from shell.definition_service.bootstrap.definition.event_registry import (
    build_definition_event_registry,
)
from shell.execution_service.bootstrap.execution.container.execution_core_container import (
    ExecutionCoreContainer,
)
from shell.execution_service.bootstrap.execution.event_registry import (
    build_execution_event_registry,
)
from shell.ingestion_service.bootstrap.ingestion.container.ingestion_core_container import (
    IngestionCoreContainer,
)
from shell.ingestion_service.bootstrap.ingestion.event_registry import (
    build_ingestion_event_registry,
)
from shell.project_service.bootstrap.project.container.project_core_container import (
    ProjectCoreContainer,
)
from shell.project_service.bootstrap.project.event_registry import build_project_event_registry
from shell.scheduling_service.bootstrap.scheduling.container.scheduling_core_container import (
    SchedulingCoreContainer,
)
from shell.scheduling_service.bootstrap.scheduling.event_registry import (
    build_scheduling_event_registry,
)
from shell.session_service.bootstrap.session.container.session_core_container import (
    SessionCoreContainer,
)
from shell.session_service.bootstrap.session.event_registry import build_session_event_registry
from shell.user_service.bootstrap.user.container.user_core_container import UserCoreContainer
from shell.user_service.bootstrap.user.event_registry import build_user_event_registry

_SERVICE_REGISTRIES: tuple[tuple[Any, Any], ...] = (
    (DefinitionCoreContainer, build_definition_event_registry),
    (ExecutionCoreContainer, build_execution_event_registry),
    (IngestionCoreContainer, build_ingestion_event_registry),
    (ProjectCoreContainer, build_project_event_registry),
    (SchedulingCoreContainer, build_scheduling_event_registry),
    (SessionCoreContainer, build_session_event_registry),
    (None, build_user_event_registry),
)

_EVENT_CONSUMERS = (
    DefinitionCoreContainer,
    ExecutionCoreContainer,
    IngestionCoreContainer,
    ProjectCoreContainer,
    SchedulingCoreContainer,
    SessionCoreContainer,
)


def test_event_transport_receives_registries_from_composition_root() -> None:
    for container_type, registry_builder in _SERVICE_REGISTRIES:
        if container_type is None:
            assert registry_builder()
            continue
        container = container_type()
        assert container.event_registry() == registry_builder()

    for container_type in _EVENT_CONSUMERS:
        container = container_type()
        container.config.db_url.from_value("sqlite+aiosqlite:///:memory:")
        processor = container.event_inbox_processor_factory()
        assert processor._inbox_model is cast(
            "Any", container.persistence_delivery_models().events.inbox
        )
        assert processor._deserializer._registry == container.event_registry()

    assert not hasattr(UserCoreContainer, "event_inbox_processor_factory")
