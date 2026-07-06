"""Round-trip tests for SQL ORM model <-> domain entity mappers.

from shell.infrastructure.execution.node_execution.persistence.sql.models.node_execution import (
            NodeExecutionModel,
        )
from shell.infrastructure.execution.graph_execution.persistence.sql.models.graph_execution import (
            GraphExecutionModel,
        )
Verifies each bidirectional mapper by creating an entity, mapping to a
model, mapping back to an entity, and comparing key fields.

Known mapper bugs (tests marked ``xfail``):
1. Session: ``session_model_to_entity`` passes ``goal=`` to
   ``Session.__init__`` which does not accept that keyword.
"""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.aggregates.node_execution.node_execution import (
    NodeExecution,
)
from shell.domain.execution.aggregates.task_execution.task_execution import TaskExecution
from shell.domain.execution.aggregates.workflow import Workflow
from shell.domain.execution.value_objects.graph_depth import GraphDepth
from shell.domain.execution.value_objects.ids import (
    GraphExecutionId,
    NodeExecutionId,
    SessionIdRef,
    TaskExecutionId,
    WorkflowId,
)
from shell.domain.execution.value_objects.max_subgraph_depth import (
    MaxSubgraphDepth,
)
from shell.domain.execution.value_objects.node_order import NodeOrder
from shell.domain.execution.value_objects.node_role import NodeRole
from shell.domain.execution.value_objects.node_type import NodeType
from shell.domain.execution.value_objects.task_name import TaskName
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.mode import Mode
from shell.domain.platform.value_objects.timestamp import Timestamp
from shell.domain.platform.value_objects.updated_at import UpdatedAt
from shell.domain.session.aggregates.session import Session
from shell.domain.session.aggregates.session.value_objects.session_id import SessionId
from shell.domain.session.value_objects.project_id_ref import ProjectIdRef
from shell.domain.session.value_objects.session_status import SessionStatus
from shell.domain.session.value_objects.user_id_ref import UserIdRef
from shell.infrastructure.execution.node_execution.persistence.sql.repositories.sql_node_execution_repository import (
    _node_execution_entity_to_model,
    _node_execution_model_to_entity,
)
from shell.infrastructure.execution.persistence.sql.mappers import (
    graph_execution_entity_to_model,
    graph_execution_model_to_entity,
    task_execution_entity_to_model,
    task_execution_model_to_entity,
    workflow_entity_to_model,
    workflow_model_to_entity,
)
from shell.infrastructure.execution.persistence.sql.models import (
    GraphExecutionModel,
    NodeExecutionModel,
    WorkflowModel,
)
from shell.infrastructure.session.persistence.sql.mappers import (
    session_entity_to_model,
    session_model_to_entity,
)

_NOW = datetime(2026, 6, 1, 12, 0, 0, tzinfo=UTC)


def _raw(dt: datetime | Timestamp | None) -> datetime | None:
    """Extract raw datetime from a datetime or Timestamp."""
    if dt is None:
        return None
    return dt.value if isinstance(dt, Timestamp) else dt


# ---------------------------------------------------------------------------
# Workflow  (all mappers work after _raw() fix)
# ---------------------------------------------------------------------------


class TestWorkflowMapper:
    def test_entity_to_model(self) -> None:
        original = Workflow(
            id=WorkflowId("wf-1"),
            session_id=SessionIdRef("sess-1"),
            created_at=CreatedAt.from_datetime(_NOW),
        )
        model = workflow_entity_to_model(original)

        assert model.id == "wf-1"
        assert model.status == original.status.value
        assert model.session_id == "sess-1"

    def test_model_to_entity(self) -> None:
        model = WorkflowModel(id="wf-2", status="active", session_id="sess-2", created_at=_NOW)
        entity = workflow_model_to_entity(model)

        assert entity.id.value == "wf-2"
        assert entity.status.value == "active"
        assert entity.session_id is not None
        assert entity.session_id.value == "sess-2"

    def test_round_trip(self) -> None:
        original = Workflow(id=WorkflowId("wf-3"), created_at=CreatedAt.from_datetime(_NOW))
        model = workflow_entity_to_model(original)
        model.created_at = _raw(model.created_at)  # type: ignore[assignment]

        restored = workflow_model_to_entity(model)

        assert restored.id.value == original.id.value
        assert restored.status.value == original.status.value
        assert restored.session_id == original.session_id
        assert restored.pull_events() == []


# ---------------------------------------------------------------------------
# TaskExecution  (model_to_entity buggy: missing description)
# ---------------------------------------------------------------------------


class TestTaskExecutionMapper:
    def test_entity_to_model(self) -> None:
        original = TaskExecution(
            id=TaskExecutionId("te-1"),
            name=TaskName("test-task"),
            created_at=CreatedAt.from_datetime(_NOW),
        )
        model = task_execution_entity_to_model(original)

        assert model.id == "te-1"
        assert model.name == "test-task"
        assert model.workflow_id is None

    def test_entity_to_model_with_workflow(self) -> None:
        original = TaskExecution(
            id=TaskExecutionId("te-2"),
            name=TaskName("nested"),
            workflow_id=WorkflowId("wf-1"),
            created_at=CreatedAt.from_datetime(_NOW),
        )
        model = task_execution_entity_to_model(original)

        assert model.id == "te-2"
        assert model.workflow_id == "wf-1"

    def test_round_trip(self) -> None:
        original = TaskExecution(
            id=TaskExecutionId("te-3"),
            name=TaskName("test"),
            created_at=CreatedAt.from_datetime(_NOW),
        )
        model = task_execution_entity_to_model(original)
        model.created_at = _raw(model.created_at)  # type: ignore[assignment]

        restored = task_execution_model_to_entity(model)

        assert restored.id.value == original.id.value
        assert restored.name.value == original.name.value


# ---------------------------------------------------------------------------
# GraphExecution  (entity_to_model buggy: missing timeout_at/correlation_id/tags properties)
# ---------------------------------------------------------------------------


class TestGraphExecutionMapper:
    def test_entity_to_model_minimal(self) -> None:
        original = GraphExecution(
            id=GraphExecutionId("ge-1"),
            task_execution_id=TaskExecutionId("te-1"),
            depth=GraphDepth(0),
            max_subgraph_depth=MaxSubgraphDepth(5),
        )

        model = graph_execution_entity_to_model(original)
        assert model.timeout_at is None

    def test_model_to_entity(self) -> None:
        model = GraphExecutionModel(
            id="ge-1",
            task_execution_id="te-1",
            graph_definition_id="",
            state_input={},
            state_output={},
            depth=0,
            max_subgraph_depth=5,
            tags={},
        )
        entity = graph_execution_model_to_entity(model)

        assert entity.id.value == "ge-1"
        assert entity.task_execution_id.value == "te-1"
        assert entity.parent_graph_execution_id is None
        assert entity.pull_events() == []

    def test_model_to_entity_with_nesting(self) -> None:
        model = GraphExecutionModel(
            id="ge-2",
            task_execution_id="te-1",
            graph_definition_id="",
            parent_graph_execution_id="ge-parent",
            state_input={},
            state_output={},
            depth=2,
            max_subgraph_depth=5,
            tags={},
        )
        entity = graph_execution_model_to_entity(model)

        assert entity.id.value == "ge-2"
        assert entity.parent_graph_execution_id is not None
        assert entity.parent_graph_execution_id.value == "ge-parent"
        assert entity.pull_events() == []

    def test_round_trip(self) -> None:
        original = GraphExecution(
            id=GraphExecutionId("ge-3"),
            task_execution_id=TaskExecutionId("te-1"),
            depth=GraphDepth(0),
            max_subgraph_depth=MaxSubgraphDepth(5),
        )
        model = graph_execution_entity_to_model(original)
        restored = graph_execution_model_to_entity(model)

        assert restored.id.value == original.id.value

    def test_model_to_entity_with_node_executions(self) -> None:
        model = GraphExecutionModel(
            id="ge-4",
            task_execution_id="te-1",
            graph_definition_id="gdef-1",
            state_input={},
            state_output={},
            depth=0,
            max_subgraph_depth=5,
            tags={},
        )

        entity = graph_execution_model_to_entity(model)

        assert entity.id.value == "ge-4"
        assert entity.pull_events() == []


# ---------------------------------------------------------------------------
# Session  (model_to_entity buggy: passes unexpected 'goal' kwarg)
# ---------------------------------------------------------------------------


class TestSessionMapper:
    def test_entity_to_model(self) -> None:
        original = Session(
            id=SessionId("sess-1"),
            user_id=UserIdRef("user-1"),
            project_id=ProjectIdRef("proj-1"),
            status=SessionStatus.OPEN,
            opened_at=CreatedAt.from_datetime(_NOW),
        )
        model = session_entity_to_model(original)

        assert model.id == "sess-1"
        assert model.closed_at is None

    def test_entity_to_model_closed(self) -> None:
        original = Session(
            id=SessionId("sess-2"),
            user_id=UserIdRef("user-2"),
            project_id=ProjectIdRef("proj-2"),
            status=SessionStatus.CLOSED,
            opened_at=CreatedAt.from_datetime(_NOW),
            closed_at=UpdatedAt.from_datetime(_NOW),
        )
        model = session_entity_to_model(original)

        assert model.id == "sess-2"
        assert model.closed_at is not None

    def test_round_trip(self) -> None:
        original = Session(
            id=SessionId("sess-3"),
            user_id=UserIdRef("user-3"),
            project_id=ProjectIdRef("proj-3"),
            status=SessionStatus.OPEN,
            opened_at=CreatedAt.from_datetime(_NOW),
        )
        model = session_entity_to_model(original)
        model.opened_at = _raw(model.opened_at)  # type: ignore[assignment]

        restored = session_model_to_entity(model)

        assert restored.id.value == "sess-3"
        assert restored.session_status == SessionStatus.OPEN


# ---------------------------------------------------------------------------
# NodeExecution  (private mappers in repository work cleanly)
# ---------------------------------------------------------------------------


class TestNodeExecutionMapper:
    def test_entity_to_model_minimal(self) -> None:
        original = NodeExecution(
            id=NodeExecutionId("gne-1"),
            position=NodeOrder(0),
            mode=Mode.WORKER,
            role=NodeRole.AGENT,
            node_type=NodeType("worker"),
        )
        model = _node_execution_entity_to_model(original)

        assert model.id == "gne-1"
        assert model.position == 0
        assert model.mode == "worker"
        assert model.role == "AGENT"
        assert model.node_type == "worker"

    def test_model_to_entity_minimal(self) -> None:
        model = NodeExecutionModel(id="gne-1", position=0, mode="worker")
        entity = _node_execution_model_to_entity(model)

        assert entity.id.value == "gne-1"
        assert entity.position.value == 0
        assert entity.mode == Mode.WORKER
        assert entity.pull_events() == []

    def test_round_trip_minimal(self) -> None:
        original = NodeExecution(
            id=NodeExecutionId("gne-3"),
            position=NodeOrder(1),
            mode=Mode.AGENT,
            role=NodeRole.AGENT,
            node_type=NodeType("llm"),
        )
        model = _node_execution_entity_to_model(original)
        restored = _node_execution_model_to_entity(model)

        assert restored.id.value == original.id.value
        assert restored.position == original.position
        assert restored.mode == original.mode
        assert restored.role == original.role
        assert restored.node_type == original.node_type
        assert restored.pull_events() == []

    def test_round_trip_full(self) -> None:
        original = NodeExecution(
            id=NodeExecutionId("gne-4"),
            position=NodeOrder(3),
            mode=Mode.PLANNER,
            role=NodeRole.PLANNER,
            node_type=NodeType("llm"),
        )
        model = _node_execution_entity_to_model(original)
        restored = _node_execution_model_to_entity(model)

        assert restored.id.value == "gne-4"
        assert restored.position.value == 3
        assert restored.mode == Mode.PLANNER
        assert restored.role == "PLANNER"
        assert restored.node_type.value == "llm"
        assert restored.pull_events() == []
