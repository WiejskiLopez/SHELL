from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from shell.domain.entities.workflow.graph_node_execution_state import (
    GraphNodeExecutionState,
)
from shell.domain.events.events import (
    DomainEvent,
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


@dataclass(slots=True)
class Workflow:
    """Workflow aggregate root — owns GraphNodeExecutionStates, NodeResults and the cursor."""

    id: WorkflowId
    task_execution_id: TaskExecutionId
    status: Status
    created_at: datetime
    cursor: WorkflowCursor = field(default_factory=WorkflowCursor.empty)
    execution_context: WorkflowExecutionContext = field(
        default_factory=WorkflowExecutionContext.empty
    )
    version: int = 0
    graph_node_execution_states: dict[str, GraphNodeExecutionState] = field(default_factory=dict)
    graph_node_execution_results: dict[str, GraphNodeExecutionResult] = field(default_factory=dict)
    _events: list[DomainEvent] = field(default_factory=list, repr=False, compare=False)

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

    def append_event(self, event: DomainEvent) -> None:
        self._events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        events = list(self._events)
        self._events.clear()
        return events

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
