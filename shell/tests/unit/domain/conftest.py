from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


from shell.domain.entities.base import AggregateRoot, Entity
from shell.domain.entities.workflow import Workflow
from shell.domain.events.events import DomainEvent
from shell.domain.value_objects.ids import WorkflowId
from shell.domain.entities.graph_execution import GraphExecution
from shell.domain.entities.graph_node_execution import GraphNodeExecution
from shell.domain.value_objects.ids import (
    GraphDefinitionId,
    GraphExecutionId,
    GraphNodeExecutionId,
    TaskExecutionId,
)
from shell.domain.value_objects.mode import Mode
from shell.domain.value_objects.workflow_execution_context import (
    WorkflowExecutionContext,
)

# ---------------------------------------------------------------------------
# Entity base test helpers (used by test_entity_identity, test_aggregate_*)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _SampleId:
    value: str


@dataclass(frozen=True, slots=True)
class _SampleEvent(DomainEvent):
    payload: str = ""


class _SampleEntity(Entity[_SampleId]):
    __slots__ = ("_label",)

    def __init__(self, id: _SampleId, label: str) -> None:
        super().__init__(id)
        self._label = label

    @property
    def label(self) -> str:
        return self._label

    def relabel(self, label: str) -> None:
        self._label = label


class _SampleAggregate(AggregateRoot[_SampleId]):
    __slots__ = ("_label",)

    def __init__(self, id: _SampleId, label: str) -> None:
        super().__init__(id)
        self._label = label

    @property
    def label(self) -> str:
        return self._label

    def do_something(self, payload: str) -> None:
        now = datetime.now(tz=UTC)
        self.append_event(_SampleEvent(occurred_at=now, payload=payload))


# ---------------------------------------------------------------------------
# Workflow step machine test helpers
# ---------------------------------------------------------------------------

_NOW = datetime(2026, 6, 1, tzinfo=UTC)


def _new_workflow() -> Workflow:
    return Workflow.new(
        id_=WorkflowId.generate(), task_execution_id=TaskExecutionId("task-id"), now=_NOW
    )


def _ctx() -> WorkflowExecutionContext:
    return WorkflowExecutionContext(work_dir="/tmp", correlation_id="cid-1")


# ---------------------------------------------------------------------------
# Navigator test helpers
# ---------------------------------------------------------------------------


def _graph_node_execution(
    graph_node_execution_id: str, position: int, mode: str = "agent"
) -> GraphNodeExecution:
    return GraphNodeExecution(
        id=GraphNodeExecutionId(graph_node_execution_id),
        position=position,
        node_dir=f"/fake/{graph_node_execution_id}",
        mode=Mode(mode),
        role=mode,
        node_type=mode,
    )


def _graph_execution(*graph_node_executions: GraphNodeExecution) -> GraphExecution:
    return GraphExecution(
        id=GraphExecutionId.generate(),
        task_execution_id=TaskExecutionId.generate(),
        graph_definition_id=GraphDefinitionId("tpl"),
        graph_node_executions=list(graph_node_executions),
    )
