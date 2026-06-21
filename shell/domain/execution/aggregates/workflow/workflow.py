from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.workflow.entities.graph_node_execution_state import (
    GraphNodeExecutionState,
)
from shell.domain.execution.aggregates.workflow.events.child_graphs_completed_event import (
    ChildGraphsCompletedEvent,
)
from shell.domain.execution.aggregates.workflow.events.graph_node_execution_advanced_event import (
    GraphNodeExecutionAdvancedEvent,
)
from shell.domain.execution.aggregates.workflow.events.graph_node_execution_completed_event import (
    GraphNodeExecutionCompletedEvent,
)
from shell.domain.execution.aggregates.workflow.events.graph_node_execution_failed_event import (
    GraphNodeExecutionFailedEvent,
)
from shell.domain.execution.aggregates.workflow.events.graph_node_execution_requested_event import (
    GraphNodeExecutionRequestedEvent,
)
from shell.domain.execution.aggregates.workflow.events.graph_node_execution_started_event import (
    GraphNodeExecutionStartedEvent,
)
from shell.domain.execution.aggregates.workflow.events.workflow_completed_event import (
    WorkflowCompletedEvent,
)
from shell.domain.execution.aggregates.workflow.events.workflow_failed_event import (
    WorkflowFailedEvent,
)
from shell.domain.execution.aggregates.workflow.events.workflow_started_event import (
    WorkflowStartedEvent,
)
from shell.domain.execution.aggregates.workflow.exceptions.invalid_workflow_transition import InvalidWorkflowTransition
from shell.domain.execution.aggregates.graph_node_execution.value_objects.workflow_cursor import WorkflowCursor
from shell.domain.execution.value_objects.workflow_execution_context import (
    WorkflowExecutionContext,
)
from shell.domain.platform.base import AggregateRoot
from shell.domain.platform.value_objects.status import Status

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.aggregates.workflow.entities.graph_node_execution_result import (
        GraphNodeExecutionResult,
    )
    from shell.domain.execution.aggregates.workflow.services.compensation_handler import CompensationHandler
    from shell.domain.execution.aggregates.graph_execution.graph_execution_id import GraphExecutionId
    from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution_id import GraphNodeExecutionId
    from shell.domain.execution.aggregates.task_execution.task_execution_id import TaskExecutionId
    from shell.domain.execution.aggregates.workflow.value_objects.ids.graph_node_execution_result_id import (
        GraphNodeExecutionResultId,
    )
    from shell.domain.execution.aggregates.workflow.workflow_id import WorkflowId


class Workflow(AggregateRoot["WorkflowId"]):
    """Workflow aggregate root — owns GraphNodeExecutionStates, NodeResults and the cursor.

    TaskExecution and GraphExecution reference this Workflow via workflow_id.
    """

    __slots__ = (
        "_status",
        "_created_at",
        "_cursor",
        "_execution_context",
        "_version",
        "_graph_node_execution_states",
        "_graph_node_execution_results",
    )

    _status: Status
    _created_at: datetime
    _cursor: WorkflowCursor
    _execution_context: WorkflowExecutionContext
    _version: int
    _graph_node_execution_states: dict[str, GraphNodeExecutionState]
    _graph_node_execution_results: dict[str, GraphNodeExecutionResult]

    def __init__(
        self,
        *,
        id: WorkflowId,
        status: Status,
        created_at: datetime,
        cursor: WorkflowCursor | None = None,
        execution_context: WorkflowExecutionContext | None = None,
        version: int = 0,
        graph_node_execution_states: dict[str, GraphNodeExecutionState] | None = None,
        graph_node_execution_results: dict[str, GraphNodeExecutionResult] | None = None,
    ) -> None:
        super().__init__(id)
        self._status = status
        self._created_at = created_at
        self._cursor = cursor if cursor is not None else WorkflowCursor.empty()
        self._execution_context = (
            execution_context if execution_context is not None else WorkflowExecutionContext.empty()
        )
        self._version = version
        self._graph_node_execution_states = graph_node_execution_states or {}
        self._graph_node_execution_results = graph_node_execution_results or {}
    @property
    def status(self) -> Status:
        return self._status

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def cursor(self) -> WorkflowCursor:
        return self._cursor

    @property
    def execution_context(self) -> WorkflowExecutionContext:
        return self._execution_context

    @property
    def version(self) -> int:
        return self._version

    @property
    def graph_node_execution_states(self) -> tuple[GraphNodeExecutionState, ...]:
        return tuple(self._graph_node_execution_states.values())

    @property
    def graph_node_execution_results(self) -> tuple[GraphNodeExecutionResult, ...]:
        return tuple(self._graph_node_execution_results.values())

    def apply_new_version(self, version: int) -> None:
        self._version = version

    def get_graph_node_execution_state(
        self, graph_node_execution_id: GraphNodeExecutionId
    ) -> GraphNodeExecutionState | None:
        return self._graph_node_execution_states.get(graph_node_execution_id.value)

    def get_graph_node_execution_result(
        self, graph_node_execution_id: GraphNodeExecutionId
    ) -> GraphNodeExecutionResult | None:
        return self._graph_node_execution_results.get(graph_node_execution_id.value)

    @classmethod
    def new(
        cls,
        *,
        id_: WorkflowId,
        now: datetime,
    ) -> Workflow:
        return cls(
            id=id_,
            status=Status.idle(),
            created_at=now,
        )

    def start_at(
        self,
        *,
        first_graph_node_execution_id: GraphNodeExecutionId,
        context: WorkflowExecutionContext,
        now: datetime,
        task_execution_id: TaskExecutionId | None = None,
    ) -> None:
        if self._status != Status.idle():
            raise InvalidWorkflowTransition(
                f"start_at requires status=idle, got {self._status.value!r}"
            )
        self._status = Status.running()
        self._execution_context = context
        self._cursor = WorkflowCursor.at(first_graph_node_execution_id)
        self.update_graph_node_execution_state(
            first_graph_node_execution_id, Status.running(), now=now
        )
        if task_execution_id is not None:
            self.append_event(WorkflowStartedEvent.now(self.id, task_execution_id, now=now))
        self.append_event(
            GraphNodeExecutionStartedEvent.now(self.id, first_graph_node_execution_id, now=now)
        )

    def advance_to(
        self, *, next_graph_node_execution_id: GraphNodeExecutionId, now: datetime
    ) -> None:
        if self._status != Status.running():
            raise InvalidWorkflowTransition(
                f"advance_to requires status=running, got {self._status.value!r}"
            )
        previous = self._cursor.current_graph_node_execution_id
        if previous is None:
            raise InvalidWorkflowTransition("advance_to requires an active cursor")
        self._cursor = WorkflowCursor.at(next_graph_node_execution_id)
        self.update_graph_node_execution_state(
            next_graph_node_execution_id, Status.running(), now=now
        )
        self.append_event(
            GraphNodeExecutionAdvancedEvent.now(
                workflow_id=self.id,
                from_graph_node_execution_id=previous,
                to_graph_node_execution_id=next_graph_node_execution_id,
                now=now,
            )
        )
        self.append_event(
            GraphNodeExecutionStartedEvent.now(self.id, next_graph_node_execution_id, now=now)
        )

    def advance_and_request(
        self, *, next_graph_node_execution_id: GraphNodeExecutionId, now: datetime
    ) -> None:
        self.advance_to(next_graph_node_execution_id=next_graph_node_execution_id, now=now)
        self.append_event(
            GraphNodeExecutionRequestedEvent.now(self.id, next_graph_node_execution_id, now=now)
        )

    def finish(self, now: datetime, task_execution_id: TaskExecutionId | None = None) -> None:
        if self._status != Status.running():
            raise InvalidWorkflowTransition(
                f"finish requires status=running, got {self._status.value!r}"
            )
        self._status = Status.done()
        self._cursor = self._cursor.cleared()
        if task_execution_id is not None:
            self.append_event(WorkflowCompletedEvent.now(self.id, task_execution_id, now=now))

    def abort(
        self,
        *,
        reason: str,
        now: datetime,
        compensation: CompensationHandler | None = None,
        task_execution_id: TaskExecutionId | None = None,
    ) -> None:
        if self._status not in (Status.running(), Status.idle()):
            raise InvalidWorkflowTransition(
                f"abort requires status in (idle,running), got {self._status.value!r}"
            )
        self._status = Status.failed()
        self._cursor = self._cursor.cleared()
        if task_execution_id is not None:
            self.append_event(WorkflowFailedEvent.now(self.id, task_execution_id, now=now))
        if compensation is not None:
            compensation.compensate(self, reason)

    def update_graph_node_execution_state(
        self,
        graph_node_execution_id: GraphNodeExecutionId,
        status: Status,
        now: datetime,
        step: int = 0,
    ) -> None:
        from shell.domain.execution.aggregates.workflow.value_objects.ids.graph_node_execution_state_id import (
            GraphNodeExecutionStateId,
        )

        existing = self._graph_node_execution_states.get(graph_node_execution_id.value)
        state_id = existing.id if existing else GraphNodeExecutionStateId.generate()
        step = existing.step if existing else step
        self._graph_node_execution_states[graph_node_execution_id.value] = GraphNodeExecutionState(
            id=state_id,
            graph_node_execution_id=graph_node_execution_id,
            status=status,
            updated_at=now,
            step=step,
        )

    def wait_for_children(
        self,
        *,
        graph_node_execution_id: GraphNodeExecutionId,
        now: datetime,
    ) -> None:
        if self._status != Status.running():
            raise InvalidWorkflowTransition(
                f"wait_for_children requires status=running, got {self._status.value!r}"
            )
        self.update_graph_node_execution_state(
            graph_node_execution_id, Status.waiting(), now=now
        )

    def record_graph_node_execution_result(
        self,
        *,
        result_id: GraphNodeExecutionResultId,
        graph_node_execution_id: GraphNodeExecutionId,
        status: Status,
        now: datetime,
        stdout: str = "",
        stderr: str = "",
        artifact_uri: str = "",
        reason: str = "",
    ) -> GraphNodeExecutionResult:
        from shell.domain.execution.aggregates.workflow.entities.graph_node_execution_result import (
            GraphNodeExecutionResult,
        )

        result = GraphNodeExecutionResult.new(
            id_=result_id,
            graph_node_execution_id=graph_node_execution_id,
            workflow_id=self.id,
            status=status,
            stdout=stdout,
            stderr=stderr,
            artifact_uri=artifact_uri,
            now=now,
        )
        self._graph_node_execution_results[graph_node_execution_id.value] = result
        self.update_graph_node_execution_state(graph_node_execution_id, status, now=now)
        if status == Status.done():
            self.append_event(
                GraphNodeExecutionCompletedEvent.now(
                    graph_node_execution_id, self.id, result_id, now=now
                )
            )
        else:
            self.append_event(
                GraphNodeExecutionFailedEvent.now(
                    graph_node_execution_id, self.id, reason or stderr, now=now
                )
            )
        return result

    def request_node_execution(
        self,
        *,
        graph_node_execution_id: GraphNodeExecutionId,
        now: datetime,
    ) -> None:
        self.update_graph_node_execution_state(graph_node_execution_id, Status.running(), now=now)
        self.append_event(
            GraphNodeExecutionRequestedEvent.now(self.id, graph_node_execution_id, now=now)
        )

    def record_child_graphs_completed(
        self,
        *,
        parent_graph_execution_id: GraphExecutionId,
        completed_child_ids: tuple[GraphExecutionId, ...],
        combined_output: dict[str, Any] | None = None,
        now: datetime | None = None,
    ) -> None:
        self.append_event(
            ChildGraphsCompletedEvent.now(
                parent_graph_execution_id=parent_graph_execution_id,
                completed_child_ids=completed_child_ids,
                combined_output=combined_output,
                now=now,
            )
        )
