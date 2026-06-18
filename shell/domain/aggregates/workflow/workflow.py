from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.aggregates.workflow.graph_node_execution_state import (
    GraphNodeExecutionState,
)
from shell.domain.entities.base import AggregateRoot
from shell.domain.events.events import (
    GraphNodeExecutionAdvanced,
    GraphNodeExecutionCompleted,
    GraphNodeExecutionFailed,
    GraphNodeExecutionStarted,
    WorkflowCompleted,
    WorkflowFailed,
    WorkflowStarted,
)
from shell.domain.exceptions import InvalidWorkflowTransition
from shell.domain.value_objects.status import Status
from shell.domain.value_objects.workflow_cursor import WorkflowCursor
from shell.domain.value_objects.workflow_execution_context import (
    WorkflowExecutionContext,
)

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.entities.graph_node_execution_result import (
        GraphNodeExecutionResult,
    )
    from shell.domain.services.compensation_handler import CompensationHandler
    from shell.domain.value_objects.ids import (
        GraphNodeExecutionId,
        GraphNodeExecutionResultId,
        GraphNodeExecutionStateId,
        TaskExecutionId,
        WorkflowId,
    )


class Workflow(AggregateRoot["WorkflowId"]):
    """Workflow aggregate root — owns GraphNodeExecutionStates, NodeResults and the cursor."""

    __slots__ = (
        "_task_execution_id",
        "_status",
        "_created_at",
        "_cursor",
        "_execution_context",
        "_version",
        "_graph_node_execution_states",
        "_graph_node_execution_results",
    )

    _task_execution_id: TaskExecutionId
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
        task_execution_id: TaskExecutionId,
        status: Status,
        created_at: datetime,
        cursor: WorkflowCursor | None = None,
        execution_context: WorkflowExecutionContext | None = None,
        version: int = 0,
        graph_node_execution_states: dict[str, GraphNodeExecutionState] | None = None,
        graph_node_execution_results: dict[str, GraphNodeExecutionResult] | None = None,
    ) -> None:
        super().__init__(id)
        self._task_execution_id = task_execution_id
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
    def task_execution_id(self) -> TaskExecutionId:
        return self._task_execution_id

    @property
    def status(self) -> Status:
        return self._status

    @status.setter
    def status(self, value: Status) -> None:
        self._status = value

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def cursor(self) -> WorkflowCursor:
        return self._cursor

    @cursor.setter
    def cursor(self, value: WorkflowCursor) -> None:
        self._cursor = value

    @property
    def execution_context(self) -> WorkflowExecutionContext:
        return self._execution_context

    @execution_context.setter
    def execution_context(self, value: WorkflowExecutionContext) -> None:
        self._execution_context = value

    @property
    def version(self) -> int:
        return self._version

    @version.setter
    def version(self, value: int) -> None:
        self._version = value

    @property
    def graph_node_execution_states(self) -> dict[str, GraphNodeExecutionState]:
        return self._graph_node_execution_states

    @property
    def graph_node_execution_results(self) -> dict[str, GraphNodeExecutionResult]:
        return self._graph_node_execution_results

    @classmethod
    def new(
        cls,
        *,
        id_: WorkflowId,
        task_execution_id: TaskExecutionId,
        now: datetime,
    ) -> Workflow:
        return cls(
            id=id_,
            task_execution_id=task_execution_id,
            status=Status.idle(),
            created_at=now,
        )

    def start_at(
        self,
        *,
        first_graph_node_execution_id: GraphNodeExecutionId,
        context: WorkflowExecutionContext,
        now: datetime,
    ) -> None:
        if self.status != Status.idle():
            raise InvalidWorkflowTransition(
                f"start_at requires status=idle, got {self.status.value!r}"
            )
        self.status = Status.running()
        self.execution_context = context
        self.cursor = WorkflowCursor.at(first_graph_node_execution_id)
        self.update_graph_node_execution_state(
            first_graph_node_execution_id, Status.running(), now=now
        )
        self.append_event(WorkflowStarted.now(self.id, self.task_execution_id, now=now))
        self.append_event(
            GraphNodeExecutionStarted.now(self.id, first_graph_node_execution_id, now=now)
        )

    def advance_to(
        self, *, next_graph_node_execution_id: GraphNodeExecutionId, now: datetime
    ) -> None:
        if self.status != Status.running():
            raise InvalidWorkflowTransition(
                f"advance_to requires status=running, got {self.status.value!r}"
            )
        previous = self.cursor.current_graph_node_execution_id
        if previous is None:
            raise InvalidWorkflowTransition("advance_to requires an active cursor")
        self.cursor = WorkflowCursor.at(next_graph_node_execution_id)
        self.update_graph_node_execution_state(
            next_graph_node_execution_id, Status.running(), now=now
        )
        self.append_event(
            GraphNodeExecutionAdvanced.now(
                workflow_id=self.id,
                from_graph_node_execution_id=previous,
                to_graph_node_execution_id=next_graph_node_execution_id,
                now=now,
            )
        )
        self.append_event(
            GraphNodeExecutionStarted.now(self.id, next_graph_node_execution_id, now=now)
        )

    def finish(self, now: datetime) -> None:
        if self.status != Status.running():
            raise InvalidWorkflowTransition(
                f"finish requires status=running, got {self.status.value!r}"
            )
        self.status = Status.done()
        self.cursor = self.cursor.cleared()
        self.append_event(WorkflowCompleted.now(self.id, self.task_execution_id, now=now))

    def abort(
        self,
        *,
        reason: str,
        now: datetime,
        compensation: CompensationHandler | None = None,
    ) -> None:
        if self.status not in (Status.running(), Status.idle()):
            raise InvalidWorkflowTransition(
                f"abort requires status in (idle,running), got {self.status.value!r}"
            )
        self.status = Status.failed()
        self.cursor = self.cursor.cleared()
        self.append_event(WorkflowFailed.now(self.id, self.task_execution_id, now=now))
        if compensation is not None:
            compensation.compensate(self, reason)

    def update_graph_node_execution_state(
        self,
        graph_node_execution_id: GraphNodeExecutionId,
        status: Status,
        now: datetime,
        step: int = 0,
    ) -> None:
        from shell.domain.value_objects.ids import GraphNodeExecutionStateId

        existing = self.graph_node_execution_states.get(graph_node_execution_id.value)
        state_id = existing.id if existing else GraphNodeExecutionStateId.generate()
        self.graph_node_execution_states[graph_node_execution_id.value] = GraphNodeExecutionState(
            id=state_id,
            graph_node_execution_id=graph_node_execution_id,
            status=status,
            updated_at=now,
            step=step,
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
        from shell.domain.entities.graph_node_execution_result import (
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
        self.graph_node_execution_results[graph_node_execution_id.value] = result
        self.update_graph_node_execution_state(graph_node_execution_id, status, now=now)
        if status == Status.done():
            self.append_event(
                GraphNodeExecutionCompleted.now(
                    graph_node_execution_id, self.id, result_id, now=now
                )
            )
        else:
            self.append_event(
                GraphNodeExecutionFailed.now(
                    graph_node_execution_id, self.id, reason or stderr, now=now
                )
            )
        return result
