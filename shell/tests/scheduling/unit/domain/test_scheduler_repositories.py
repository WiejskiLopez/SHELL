"""Tests for in-memory scheduling repositories."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.scheduling.aggregates.scheduler_definition import (
    SchedulerDefinition,
)
from shell.domain.scheduling.aggregates.scheduler_execution import (
    SchedulerExecution,
)
from shell.domain.scheduling.value_objects.action_config import ActionConfig
from shell.domain.scheduling.value_objects.execution_status import ExecutionStatus
from shell.domain.scheduling.value_objects.ids import (
    SchedulerDefinitionId,
    SchedulerExecutionId,
)
from shell.domain.scheduling.value_objects.trigger_config import TriggerConfig
from shell.infrastructure.scheduling.persistence.memory.in_memory_scheduler_definition_repository import (
    InMemorySchedulerDefinitionRepository,
)
from shell.infrastructure.scheduling.persistence.memory.in_memory_scheduler_execution_repository import (
    InMemorySchedulerExecutionRepository,
)


class TestInMemorySchedulerDefinitionRepository:
    def setup_method(self) -> None:
        self._repo = InMemorySchedulerDefinitionRepository()
        self._now = datetime.now(UTC)

    async def test_save_and_get_by_id(self) -> None:
        definition = self._make_definition("def-1")
        await self._repo.save(definition)

        result = await self._repo.get_by_id(SchedulerDefinitionId("def-1"))
        assert result is not None
        assert result.name == "test-def"

    async def test_get_by_id_not_found(self) -> None:
        result = await self._repo.get_by_id(SchedulerDefinitionId("nonexistent"))
        assert result is None

    async def test_find_by_trigger(self) -> None:
        d1 = self._make_definition("def-1", source_context="execution", event_type="EvtA")
        d2 = self._make_definition("def-2", source_context="execution", event_type="EvtA")
        d3 = self._make_definition("def-3", source_context="definition", event_type="EvtB")
        await self._repo.save(d1)
        await self._repo.save(d2)
        await self._repo.save(d3)

        results = await self._repo.find_by_trigger("execution", "EvtA")
        assert len(results) == 2
        assert {r.id.value for r in results} == {"def-1", "def-2"}

    async def test_find_by_trigger_no_match(self) -> None:
        d1 = self._make_definition("def-1", source_context="execution", event_type="EvtA")
        await self._repo.save(d1)

        results = await self._repo.find_by_trigger("definition", "EvtA")
        assert len(results) == 0

    @staticmethod
    def _make_definition(
        id: str,
        source_context: str = "execution",
        event_type: str = "TestEvent",
    ) -> SchedulerDefinition:
        return SchedulerDefinition(
            id=SchedulerDefinitionId(id),
            name="test-def",
            trigger_config=TriggerConfig(
                source_context=source_context,
                trigger_event_type=event_type,
            ),
            action_config=ActionConfig(action_type="spawn_graph"),
        )


class TestInMemorySchedulerExecutionRepository:
    def setup_method(self) -> None:
        self._repo = InMemorySchedulerExecutionRepository()
        self._now = datetime.now(UTC)

    async def test_save_and_get_by_id(self) -> None:
        execution = self._make_execution("exec-1")
        await self._repo.save(execution)

        result = await self._repo.get_by_id(SchedulerExecutionId("exec-1"))
        assert result is not None
        assert result.status == ExecutionStatus.PENDING

    async def test_get_by_action_ref(self) -> None:
        e1 = self._make_execution("exec-1", action_ref="graph-1")
        e2 = self._make_execution("exec-2", action_ref="graph-2")
        e3 = self._make_execution("exec-3", action_ref="graph-1")
        await self._repo.save(e1)
        await self._repo.save(e2)
        await self._repo.save(e3)

        results = await self._repo.get_by_action_ref("graph-1")
        assert len(results) == 2

    async def test_count_by_definition_and_status(self) -> None:
        e1 = self._make_execution("exec-1", def_id="def-1", status="executing")
        e2 = self._make_execution("exec-2", def_id="def-1", status="executing")
        e3 = self._make_execution("exec-3", def_id="def-1", status="completed")
        await self._repo.save(e1)
        await self._repo.save(e2)
        await self._repo.save(e3)

        count = await self._repo.count_by_definition_and_status("def-1", "executing")
        assert count == 2

    @staticmethod
    def _make_execution(
        id: str,
        def_id: str = "def-1",
        action_ref: str | None = None,
        status: str = "pending",
    ) -> SchedulerExecution:
        return SchedulerExecution(
            id=SchedulerExecutionId(id),
            scheduler_definition_id=SchedulerDefinitionId(def_id),
            status=ExecutionStatus(status),
            action_ref=action_ref,
            action_ref_type="graph_execution",
        )
