from __future__ import annotations

from shell.scheduling.bootstrap.scheduling.container.scheduling_core_container import (
    SchedulingCoreContainer,
)


def test_event_inbox_processor_uses_scheduling_event_registry() -> None:
    container = SchedulingCoreContainer()
    container.config.db_url.from_value("sqlite+aiosqlite:///test.db")

    registry = container.event_registry()
    processor = container.event_inbox_processor_factory()

    assert processor._deserializer._registry is registry
    assert "SchedulerExecutionStartedIntegrationEvent" in registry
