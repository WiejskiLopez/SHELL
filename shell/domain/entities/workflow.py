"""Workflow aggregate.

A Workflow owns its NodeStates, NodeResults and the **execution cursor**
(``WorkflowCursor``) that points to the node currently being executed.

State machine (see ``docs/dokumentacja/workflow-execution-flow.md``)::

    new() -> idle
       │ start_at(first, ctx)         WorkflowStarted + NodeStarted
       ▼
    running ────────────────────────┐
       │ record_node_result(ok)    │ NodeCompleted
       │ advance_to(next)           │ NodeAdvanced + NodeStarted
       └──── back to running ───────┘
       │ record_node_result(ok) + finish()      WorkflowCompleted
       ▼
    done

       record_node_result(failed) + abort()     WorkflowFailed
       │
       ▼
    failed

Every save through the repository increments ``Workflow.version`` atomically
as part of the CAS (compare-and-swap) update so concurrent writers are
detected via ``WorkflowConcurrentlyModified``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from shell.domain.events.events import (
    DomainEvent,
    NodeAdvanced,
    NodeCompleted,
    NodeFailed,
    NodeStarted,
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

    from shell.domain.entities.node_result import NodeResult
    from shell.domain.services.compensation_handler import CompensationHandler
    from shell.domain.value_objects.ids import (
        NodeId,
        NodeResultId,
        NodeStateId,
        WorkflowId, TaskId,
)


@dataclass(slots=True)
class NodeState:
    id: NodeStateId
    node_id: NodeId
    status: Status
    updated_at: datetime
    step: int = 0


@dataclass(slots=True)
class Workflow:
    """Workflow aggregate root — owns NodeStates, NodeResults and the cursor."""

    id: WorkflowId
    task_id: TaskId
    status: Status
    created_at: datetime
    cursor: WorkflowCursor = field(default_factory=WorkflowCursor.empty)
    execution_context: WorkflowExecutionContext = field(
        default_factory=WorkflowExecutionContext.empty
    )
    version: int = 0
    node_states: dict[str, NodeState] = field(default_factory=dict)
    node_results: dict[str, NodeResult] = field(default_factory=dict)
    _events: list[DomainEvent] = field(default_factory=list, repr=False, compare=False)

    @classmethod
    def new(
        cls,
        *,
        id_: WorkflowId,
        task_id: TaskId,
        now: datetime,
    ) -> Workflow:
        return cls(
            id=id_,
            task_id=task_id,
            status=Status.idle(),
            created_at=now,
        )

    # ── Domain event accumulation ──────────────────────────────────────────

    def append_event(self, event: DomainEvent) -> None:
        self._events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        events = list(self._events)
        self._events.clear()
        return events

    # ── Concurrency token ──────────────────────────────────────────────────
    # ``version`` mirrors the persisted concurrency token. It is **not** bumped
    # by aggregate methods — the repository increments it atomically on save
    # (CAS WHERE version = expected). Aggregates therefore stay free of
    # persistence concerns and unit tests can verify state transitions in
    # isolation from the optimistic-locking machinery.

    # ── State-machine transitions ──────────────────────────────────────────

    def start_at(
        self,
        *,
        first_node_id: NodeId,
        context: WorkflowExecutionContext,
        now: datetime,
    ) -> None:
        """Begin execution and place the cursor on ``first_node_id``.

        Emits ``WorkflowStarted`` (idle → running) and ``NodeStarted``
        (cursor entered ``first_node_id``).
        """
        if self.status != Status.idle():
            raise InvalidWorkflowTransition(
                f"start_at requires status=idle, got {self.status.value!r}"
            )
        self.status = Status.running()
        self.execution_context = context
        self.cursor = WorkflowCursor.at(first_node_id)
        self.update_node_state(first_node_id, Status.running(), now=now)
        self.append_event(WorkflowStarted.now(self.id, self.task_id, now=now))
        self.append_event(NodeStarted.now(self.id, first_node_id, now=now))

    def advance_to(self, *, next_node_id: NodeId, now: datetime) -> None:
        """Move the cursor from the current node to ``next_node_id``.

        Emits ``NodeAdvanced`` and ``NodeStarted``. Caller is responsible for
        having already recorded the result of the previous node.
        """
        if self.status != Status.running():
            raise InvalidWorkflowTransition(
                f"advance_to requires status=running, got {self.status.value!r}"
            )
        previous = self.cursor.current_node_id
        if previous is None:
            raise InvalidWorkflowTransition("advance_to requires an active cursor")
        self.cursor = WorkflowCursor.at(next_node_id)
        self.update_node_state(next_node_id, Status.running(), now=now)
        self.append_event(
            NodeAdvanced.now(
                workflow_id=self.id,
                from_node_id=previous,
                to_node_id=next_node_id,
                now=now,
            )
        )
        self.append_event(NodeStarted.now(self.id, next_node_id, now=now))

    def finish(self, now: datetime) -> None:
        """Mark the workflow as completed (terminal state)."""
        if self.status != Status.running():
            raise InvalidWorkflowTransition(
                f"finish requires status=running, got {self.status.value!r}"
            )
        self.status = Status.done()
        self.cursor = self.cursor.cleared()
        self.append_event(WorkflowCompleted.now(self.id, self.task_id, now=now))

    def abort(
        self,
        *,
        reason: str,
        now: datetime,
        compensation: CompensationHandler | None = None,
    ) -> None:
        """Mark the workflow as failed (terminal state).

        Optionally invokes a Saga ``CompensationHandler`` after the state
        transition is recorded.
        """
        if self.status not in (Status.running(), Status.idle()):
            raise InvalidWorkflowTransition(
                f"abort requires status in (idle,running), got {self.status.value!r}"
            )
        self.status = Status.failed()
        self.cursor = self.cursor.cleared()
        self.append_event(WorkflowFailed.now(self.id, self.task_id, now=now))
        if compensation is not None:
            compensation.compensate(self, reason)

    # ── Node-state / NodeResult management ─────────────────────────────────

    def update_node_state(self, node_id: NodeId, status: Status, now: datetime, step: int = 0) -> None:
        from shell.domain.value_objects.ids import NodeStateId

        existing = self.node_states.get(node_id.value)
        state_id = existing.id if existing else NodeStateId.generate()
        self.node_states[node_id.value] = NodeState(
            id=state_id,
            node_id=node_id,
            status=status,
            updated_at=now,
            step=step,
        )

    def record_node_result(
        self,
        *,
        result_id: NodeResultId,
        node_id: NodeId,
        status: Status,
        now: datetime,
        stdout: str = "",
        stderr: str = "",
        artifact_uri: str = "",
        reason: str = "",
    ) -> NodeResult:
        """Append a NodeResult, sync the matching NodeState and emit
        ``NodeCompleted`` or ``NodeFailed``.

        Records the outcome of a node execution but does **not** move the
        cursor — call :meth:`advance_to` / :meth:`finish` / :meth:`abort`
        afterwards to perform the next state transition.
        """
        from shell.domain.entities.node_result import NodeResult

        result = NodeResult.new(
            id_=result_id,
            node_id=node_id,
            workflow_id=self.id,
            status=status,
            stdout=stdout,
            stderr=stderr,
            artifact_uri=artifact_uri,
            now=now,
        )
        self.node_results[node_id.value] = result
        self.update_node_state(node_id, status, now=now)
        if status == Status.done():
            self.append_event(NodeCompleted.now(node_id, self.id, result_id, now=now))
        else:
            self.append_event(
                NodeFailed.now(node_id, self.id, reason or stderr, now=now)
            )
        return result
