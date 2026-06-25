"""Tests for SchedulerOrchestrator."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.scheduling.aggregates.scheduler_definition.scheduler_definition import (
    SchedulerDefinition,
)
from shell.domain.scheduling.aggregates.scheduler_execution.scheduler_execution import (
    SchedulerExecution,
)
from shell.domain.scheduling.services.scheduler_orchestrator import (
    SchedulerOrchestrator,
)
from shell.domain.scheduling.value_objects.action_config import ActionConfig
from shell.domain.scheduling.aggregates.scheduler_execution.value_objects.execution_status import ExecutionStatus
from shell.domain.scheduling.value_objects.ids import (
    SchedulerDefinitionId,
    SchedulerExecutionId,
)
from shell.domain.scheduling.value_objects.trigger_config import TriggerConfig


class TestSchedulerOrchestrator:
    def setup_method(self) -> None:
        self._orchestrator = SchedulerOrchestrator()
        self._now = datetime.now(UTC)

    def test_evaluate_definition_can_execute_returns_pending(self) -> None:
        definition = self._make_definition(action_type="spawn_graph", graph_definition_id="graph-1")
        execution = self._orchestrator.evaluate_definition(
            definition=definition,
            trigger_event_id="evt-1",
            trigger_event_type="TestEvent",
            input_state={"key": "value"},
            can_execute=True,
            now=self._now,
        )
        assert execution.status == ExecutionStatus.PENDING
        assert execution.trigger_event_id == "evt-1"
        assert execution.trigger_event_type == "TestEvent"
        assert execution.input_state == {"key": "value"}

    def test_evaluate_definition_cannot_execute_returns_skipped(self) -> None:
        definition = self._make_definition(action_type="spawn_graph", graph_definition_id="graph-1")
        execution = self._orchestrator.evaluate_definition(
            definition=definition,
            can_execute=False,
            now=self._now,
        )
        assert execution.status == ExecutionStatus.SKIPPED
        events = execution.pull_events()
        assert len(events) == 1
        assert "SchedulerExecutionSkippedEvent" in type(events[0]).__name__

    def test_evaluate_definition_unsupported_action_returns_skipped(
        self,
    ) -> None:
        definition = self._make_definition(action_type="unknown_action", graph_definition_id=None)
        execution = self._orchestrator.evaluate_definition(
            definition=definition,
            can_execute=True,
            now=self._now,
        )
        assert execution.status == ExecutionStatus.SKIPPED

    def test_evaluate_definition_no_graph_id_returns_skipped(self) -> None:
        definition = self._make_definition(action_type="spawn_graph", graph_definition_id=None)
        execution = self._orchestrator.evaluate_definition(
            definition=definition,
            can_execute=True,
            now=self._now,
        )
        assert execution.status == ExecutionStatus.SKIPPED

    def test_start_execution_marks_as_executing(self) -> None:
        definition = self._make_definition(action_type="spawn_graph", graph_definition_id="graph-1")
        execution = self._orchestrator.evaluate_definition(
            definition=definition,
            can_execute=True,
            now=self._now,
        )
        assert execution.status == ExecutionStatus.PENDING

        events = self._orchestrator.start_execution(
            execution,
            action_ref="graph-exec-1",
            action_ref_type="graph_execution",
            now=self._now,
        )
        assert execution.status == ExecutionStatus.EXECUTING  # type: ignore[comparison-overlap]
        assert execution.action_ref == "graph-exec-1"
        assert execution.action_ref_type == "graph_execution"
        assert len(events) == 1
        assert "SchedulerExecutionStartedEvent" in type(events[0]).__name__

    def test_complete_execution(self) -> None:
        execution = SchedulerExecution(
            id=SchedulerExecutionId.generate(),
            scheduler_definition_id=SchedulerDefinitionId("def-1"),
            status=ExecutionStatus.EXECUTING,
            action_ref="graph-exec-1",
            action_ref_type="graph_execution",
            created_at=self._now,
            updated_at=self._now,
        )

        events = self._orchestrator.complete_execution(
            execution,
            output_state={"result": "ok"},
            error=None,
            now=self._now,
        )
        assert execution.status == ExecutionStatus.COMPLETED
        assert execution.output_state == {"result": "ok"}
        assert len(events) == 1
        assert "SchedulerExecutionCompletedEvent" in type(events[0]).__name__

    def test_fail_execution(self) -> None:
        execution = SchedulerExecution(
            id=SchedulerExecutionId.generate(),
            scheduler_definition_id=SchedulerDefinitionId("def-1"),
            status=ExecutionStatus.EXECUTING,
            action_ref="graph-exec-1",
            action_ref_type="graph_execution",
            created_at=self._now,
            updated_at=self._now,
        )

        events = self._orchestrator.complete_execution(
            execution,
            output_state=None,
            error="something went wrong",
            now=self._now,
        )
        assert execution.status == ExecutionStatus.FAILED
        assert execution.error == "something went wrong"
        assert len(events) == 1
        assert "SchedulerExecutionFailedEvent" in type(events[0]).__name__

    @staticmethod
    def _make_definition(
        action_type: str = "spawn_graph",
        graph_definition_id: str | None = None,
    ) -> SchedulerDefinition:
        return SchedulerDefinition(
            id=SchedulerDefinitionId.generate(),
            name="test-def",
            trigger_config=TriggerConfig(
                source_context="execution",
                trigger_event_type="TestEvent",
            ),
            action_config=ActionConfig(
                action_type=action_type,
                graph_definition_id=graph_definition_id,
            ),
        )
