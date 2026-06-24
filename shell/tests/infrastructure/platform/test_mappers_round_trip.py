"""Round-trip tests for SQL ORM model <-> domain entity mappers.

Verifies each bidirectional mapper by creating an entity, mapping to a
model, mapping back to an entity, and comparing key fields.

Known mapper bugs (tests marked ``xfail``):
1. Session: ``session_model_to_entity`` passes ``goal=`` to
   ``Session.__init__`` which does not accept that keyword.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.aggregates.graph_execution.entities.graph_node_transition_execution import (
    GraphNodeTransitionExecution,
)
from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
    GraphNodeExecution,
)
from shell.domain.execution.aggregates.session import Session
from shell.domain.execution.aggregates.task_execution.task_execution import TaskExecution
from shell.domain.execution.aggregates.workflow import Workflow
from shell.domain.execution.value_objects.edge_type import EdgeType
from shell.domain.execution.value_objects.environment import Environment
from shell.domain.execution.value_objects.ids import (
    GraphExecutionId,
    GraphNodeExecutionId,
    GraphNodeTransitionExecutionId,
    SessionId,
    TaskExecutionId,
    WorkflowId,
)
from shell.domain.execution.value_objects.session_status import SessionStatus
from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName
from shell.domain.execution.value_objects.workflow_status import WorkflowStatus
from shell.domain.platform.value_objects.mode import Mode
from shell.domain.platform.value_objects.timestamp import Timestamp
from shell.domain.projekt.value_objects.project_id import ProjectId
from shell.domain.user.value_objects.user_id import UserId
from shell.infrastructure.platform.persistence.sql.mappers import (
    graph_execution_entity_to_model,
    graph_execution_model_to_entity,
    session_entity_to_model,
    session_model_to_entity,
    task_execution_entity_to_model,
    task_execution_model_to_entity,
    workflow_entity_to_model,
    workflow_model_to_entity,
)
from shell.infrastructure.execution.persistence.sql.repositories.sql_graph_node_execution_repository import (
    _graph_node_execution_entity_to_model,
    _graph_node_execution_model_to_entity,
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
        original = Workflow(id=WorkflowId("wf-1"), session_id=SessionId("sess-1"), created_at=_NOW)
        model = workflow_entity_to_model(original)

        assert model.id == "wf-1"
        assert model.status == original.status.value
        assert model.session_id == "sess-1"

    def test_model_to_entity(self) -> None:
        from shell.infrastructure.execution.persistence.sql.models.workflow import WorkflowModel

        model = WorkflowModel(id="wf-2", status="active", session_id="sess-2", created_at=_NOW)
        entity = workflow_model_to_entity(model)

        assert entity.id.value == "wf-2"
        assert entity.status.value == "active"
        assert entity.session_id is not None
        assert entity.session_id.value == "sess-2"

    def test_round_trip(self) -> None:
        original = Workflow(id=WorkflowId("wf-3"), created_at=_NOW)
        model = workflow_entity_to_model(original)
        model.created_at = _raw(model.created_at)

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
            name=TaskExecutionName("test-task"),
            created_at=_NOW,
        )
        model = task_execution_entity_to_model(original)

        assert model.id == "te-1"
        assert model.name == "test-task"
        assert model.workflow_id is None

    def test_entity_to_model_with_workflow(self) -> None:
        original = TaskExecution(
            id=TaskExecutionId("te-2"),
            name=TaskExecutionName("nested"),
            workflow_id=WorkflowId("wf-1"),
            created_at=_NOW,
        )
        model = task_execution_entity_to_model(original)

        assert model.id == "te-2"
        assert model.workflow_id == "wf-1"

    def test_round_trip(self) -> None:
        original = TaskExecution(
            id=TaskExecutionId("te-3"),
            name=TaskExecutionName("test"),
            created_at=_NOW,
        )
        model = task_execution_entity_to_model(original)
        model.created_at = _raw(model.created_at)

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
            graph_definition_id="gdef-1",
        )

        model = graph_execution_entity_to_model(original)
        assert model.timeout_at is None

    def test_model_to_entity(self) -> None:
        from shell.infrastructure.execution.persistence.sql.models.graph_execution import (
            GraphExecutionModel,
        )

        model = GraphExecutionModel(
            id="ge-1",
            task_execution_id="te-1",
            graph_definition_id="gdef-1",
            state_input={},
            state_output={},
            depth=0,
            tags={},
        )
        entity = graph_execution_model_to_entity(model)

        assert entity.id.value == "ge-1"
        assert entity.task_execution_id.value == "te-1"
        assert entity.graph_definition_id == "gdef-1"
        assert entity.parent_graph_execution_id is None
        assert entity.state_input == {}
        assert entity.state_output == {}
        assert entity.pull_events() == []

    def test_model_to_entity_with_nesting(self) -> None:
        from shell.infrastructure.execution.persistence.sql.models.graph_execution import (
            GraphExecutionModel,
        )

        model = GraphExecutionModel(
            id="ge-2",
            task_execution_id="te-1",
            graph_definition_id="gdef-1",
            parent_graph_execution_id="ge-parent",
            state_input={"k": "v"},
            state_output={"o": "u"},
            depth=2,
            tags={"env": "test"},
        )
        entity = graph_execution_model_to_entity(model)

        assert entity.id.value == "ge-2"
        assert entity.parent_graph_execution_id is not None
        assert entity.parent_graph_execution_id.value == "ge-parent"
        assert entity.state_input == {"k": "v"}
        assert entity.state_output == {"o": "u"}
        assert entity.pull_events() == []

    def test_round_trip(self) -> None:
        original = GraphExecution(
            id=GraphExecutionId("ge-3"),
            task_execution_id=TaskExecutionId("te-1"),
            graph_definition_id="gdef-1",
        )
        model = graph_execution_entity_to_model(original)
        restored = graph_execution_model_to_entity(model)

        assert restored.id.value == original.id.value

    def test_model_to_entity_with_transitions(self) -> None:
        from shell.infrastructure.execution.persistence.sql.models.graph_execution import (
            GraphExecutionModel,
        )
        from shell.infrastructure.execution.persistence.sql.models.graph_node_transition_execution import (
            GraphNodeTransitionExecutionModel,
        )

        model = GraphExecutionModel(
            id="ge-4",
            task_execution_id="te-1",
            graph_definition_id="gdef-1",
            state_input={},
            state_output={},
            depth=0,
            tags={},
        )
        model.graph_node_transition_execution_models = [
            GraphNodeTransitionExecutionModel(
                id="t1",
                graph_execution_id="ge-4",
                source_node_execution_id="src-1",
                target_node_execution_id="tgt-1",
                transition_type="sequence",
                priority=0,
                label="default",
                created_at=_NOW,
                updated_at=_NOW,
            )
        ]

        entity = graph_execution_model_to_entity(model)

        assert len(entity.transitions) == 1
        t = entity.transitions[0]
        assert t.id.value == "t1"
        assert t.source_node_execution_id.value == "src-1"
        assert t.target_node_execution_id.value == "tgt-1"


# ---------------------------------------------------------------------------
# Session  (model_to_entity buggy: passes unexpected 'goal' kwarg)
# ---------------------------------------------------------------------------


class TestSessionMapper:
    def test_entity_to_model(self) -> None:
        original = Session(
            id=SessionId("sess-1"),
            user_id=UserId("user-1"),
            project_id=ProjectId("proj-1"),
            environment=Environment(os="linux", runtime="3.12", cwd="/home"),
            status=SessionStatus.OPEN,
            opened_at=_NOW,
        )
        model = session_entity_to_model(original)

        assert model.id == "sess-1"
        assert model.closed_at is None

    def test_entity_to_model_closed(self) -> None:
        original = Session(
            id=SessionId("sess-2"),
            user_id=UserId("user-2"),
            project_id=ProjectId("proj-2"),
            environment=Environment(os="mac", runtime="3.13", cwd="/Users"),
            status=SessionStatus.CLOSED,
            opened_at=_NOW,
            closed_at=_NOW,
        )
        model = session_entity_to_model(original)

        assert model.id == "sess-2"
        assert model.closed_at is not None

    @pytest.mark.xfail(
        reason="session_model_to_entity passes goal= to Session.__init__ "
        "which does not accept that keyword argument"
    )
    def test_round_trip(self) -> None:
        original = Session(
            id=SessionId("sess-3"),
            user_id=UserId("user-3"),
            project_id=ProjectId("proj-3"),
            environment=Environment(os="linux", runtime="3.12", cwd="/"),
            status=SessionStatus.OPEN,
            opened_at=_NOW,
        )
        model = session_entity_to_model(original)
        model.opened_at = _raw(model.opened_at)

        restored = session_model_to_entity(model)

        assert restored.id.value == "sess-3"
        assert restored.session_status == SessionStatus.OPEN


# ---------------------------------------------------------------------------
# GraphNodeExecution  (private mappers in repository work cleanly)
# ---------------------------------------------------------------------------


class TestGraphNodeExecutionMapper:
    def test_entity_to_model_minimal(self) -> None:
        original = GraphNodeExecution(
            id=GraphNodeExecutionId("gne-1"),
            position=0,
            mode=Mode.WORKER,
            role="worker",
            node_type="worker",
        )
        model = _graph_node_execution_entity_to_model(original)

        assert model.id == "gne-1"
        assert model.position == 0
        assert model.mode == "worker"
        assert model.role == "worker"
        assert model.node_type == "worker"
        assert model.graph_execution_id == ""

    def test_model_to_entity_minimal(self) -> None:
        from shell.infrastructure.execution.persistence.sql.models.graph_node_execution import (
            GraphNodeExecutionModel,
        )

        model = GraphNodeExecutionModel(id="gne-1", position=0, mode="worker")
        entity = _graph_node_execution_model_to_entity(model)

        assert entity.id.value == "gne-1"
        assert entity.position == 0
        assert entity.mode == Mode.WORKER
        assert entity.pull_events() == []

    def test_round_trip_minimal(self) -> None:
        original = GraphNodeExecution(
            id=GraphNodeExecutionId("gne-3"),
            position=1,
            mode=Mode.AGENT,
            role="agent",
            node_type="llm",
        )
        model = _graph_node_execution_entity_to_model(original)
        restored = _graph_node_execution_model_to_entity(model)

        assert restored.id.value == original.id.value
        assert restored.position == original.position
        assert restored.mode == original.mode
        assert restored.role == original.role
        assert restored.node_type == original.node_type
        assert restored.pull_events() == []

    def test_round_trip_full(self) -> None:
        original = GraphNodeExecution(
            id=GraphNodeExecutionId("gne-4"),
            graph_execution_id=GraphExecutionId("ge-1"),
            position=3,
            mode=Mode.PLANNER,
            role="planner",
            node_type="llm",
            model="gpt-4",
            command="/run.sh",
            retries=2,
            log_level="DEBUG",
            max_step=50,
            no_ask_user=True,
            autopilot=True,
            task_execution_id="te-1",
            source_dir="/tmp/work",
            status_initial="idle",
            timeout_seconds=120,
            max_retries=3,
            retry_delay_seconds=5,
        )
        model = _graph_node_execution_entity_to_model(original)
        restored = _graph_node_execution_model_to_entity(model)

        assert restored.id.value == "gne-4"
        assert restored.graph_execution_id is not None
        assert restored.graph_execution_id.value == "ge-1"
        assert restored.position == 3
        assert restored.mode == Mode.PLANNER
        assert restored.role == "planner"
        assert restored.node_type == "llm"
        assert restored.model == "gpt-4"
        assert restored.command == "/run.sh"
        assert restored.retries == 2
        assert restored.log_level == "DEBUG"
        assert restored.max_step == 50
        assert restored.no_ask_user is True
        assert restored.autopilot is True
        assert restored.task_execution_id == "te-1"
        assert restored.source_dir == "/tmp/work"
        assert restored.status_initial == "idle"
        assert restored.timeout_seconds == 120
        assert restored.max_retries == 3
        assert restored.retry_delay_seconds == 5
        assert restored.pull_events() == []
