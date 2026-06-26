from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import TaskExecutionId
from shell.domain.execution.value_objects.graph_depth import GraphDepth
from shell.domain.execution.value_objects.graph_execution_status import GraphExecutionStatus
from shell.domain.execution.value_objects.max_subgraph_depth import MaxSubgraphDepth
from shell.domain.execution.value_objects.reason import Reason
from shell.domain.platform.base.aggregate_root import AggregateRoot

if TYPE_CHECKING:
    from datetime import datetime


class GraphExecution(AggregateRoot[GraphExecutionId]):
    __slots__ = (
        "_task_execution_id",
        "_parent_graph_execution_id",
        "_depth",
        "_max_subgraph_depth",
        "_status",
    )

    def __init__(
        self,
        id: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        parent_graph_execution_id: GraphExecutionId | None = None,
        depth: int = 0,
        max_subgraph_depth: int = 5,
    ) -> None:
        super().__init__(id)
        self._task_execution_id = task_execution_id
        self._parent_graph_execution_id = parent_graph_execution_id
        self._depth = GraphDepth(depth)
        self._max_subgraph_depth = MaxSubgraphDepth(max_subgraph_depth)
        self._status = GraphExecutionStatus.PENDING

    @classmethod
    def restore(
        cls,
        id: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        parent_graph_execution_id: GraphExecutionId | None = None,
        depth: int = 0,
        max_subgraph_depth: int = 5,
    ) -> Self:
        return cls(
            id=id,
            task_execution_id=task_execution_id,
            parent_graph_execution_id=parent_graph_execution_id,
            depth=depth,
            max_subgraph_depth=max_subgraph_depth,
        )

    # --- V3 FSM ---

    def start_planning(self, now: datetime) -> None:
        if self._status != GraphExecutionStatus.PENDING:
            raise InvalidGraphStateError(
                f"Cannot start planning in status {self._status}"
            )
        self._status = GraphExecutionStatus.PLANNING
        from shell.domain.execution.aggregates.graph_execution.events.graph_execution_planning_started_event import (
            GraphExecutionPlanningStartedEvent,
        )

        self.append_event(
            GraphExecutionPlanningStartedEvent.now(
                graph_execution_id=self._id,
                now=now,
            )
        )

    def plan_complete(self, plan: dict[str, Any] | None, now: datetime) -> None:
        if self._status != GraphExecutionStatus.PLANNING:
            raise InvalidGraphStateError(
                f"Cannot complete planning in status {self._status}"
            )
        self._status = GraphExecutionStatus.EXECUTING
        from shell.domain.execution.aggregates.graph_execution.events.graph_execution_planned_event import (
            GraphExecutionPlannedEvent,
        )

        self.append_event(
            GraphExecutionPlannedEvent.now(
                graph_execution_id=self._id,
                now=now,
                plan=plan,
            )
        )

    def complete(self, verifier_result: dict[str, Any] | None, now: datetime) -> None:
        if self._status != GraphExecutionStatus.VERIFYING:
            raise InvalidGraphStateError(
                f"Cannot complete graph in status {self._status}"
            )
        self._status = GraphExecutionStatus.COMPLETED
        from shell.domain.execution.aggregates.graph_execution.events.graph_execution_completed_event import (
            GraphExecutionCompletedEvent,
        )

        self.append_event(
            GraphExecutionCompletedEvent.now(
                graph_execution_id=self._id,
                now=now,
                verifier_result=verifier_result,
            )
        )

    def fail(self, reason: Reason, now: datetime) -> None:
        if self.status not in (
            GraphExecutionStatus.PLANNING,
            GraphExecutionStatus.EXECUTING,
            GraphExecutionStatus.VERIFYING,
            GraphExecutionStatus.SUSPENDED,
        ):
            raise InvalidGraphStateError(
                f"Cannot fail graph in status {self._status}"
            )
        self._status = GraphExecutionStatus.FAILED
        from shell.domain.execution.aggregates.graph_execution.events.graph_execution_failed_event import (
            GraphExecutionFailedEvent,
        )

        self.append_event(
            GraphExecutionFailedEvent.now(
                graph_execution_id=self._id,
                now=now,
                reason=reason,
            )
        )

    def mark_verifying(self, now: datetime) -> None:
        if self._status != GraphExecutionStatus.EXECUTING:
            raise InvalidGraphStateError(
                f"Cannot start verifying in status {self._status}"
            )
        self._status = GraphExecutionStatus.VERIFYING

    def suspend(self, now: datetime) -> None:
        if self._status != GraphExecutionStatus.EXECUTING:
            raise InvalidGraphStateError(
                f"Cannot suspend graph in status {self._status}"
            )
        self._status = GraphExecutionStatus.SUSPENDED

    def resume(self, now: datetime) -> None:
        if self._status != GraphExecutionStatus.SUSPENDED:
            raise InvalidGraphStateError(
                f"Cannot resume graph in status {self._status}"
            )
        self._status = GraphExecutionStatus.EXECUTING

    # --- Factory methods ---

    @classmethod
    def create_main_round(
        cls,
        id_: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        depth: int = 0,
        max_subgraph_depth: int = 5,
    ) -> GraphExecution:
        instance = cls(
            id=id_,
            task_execution_id=task_execution_id,
            parent_graph_execution_id=None,
            depth=depth,
            max_subgraph_depth=max_subgraph_depth,
        )
        return instance

    @classmethod
    def create_sub_graph(
        cls,
        id_: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        parent_id: GraphExecutionId,
        parent_depth: int,
        max_subgraph_depth: int = 5,
    ) -> GraphExecution:
        depth_val = parent_depth + 1
        if depth_val > max_subgraph_depth:
            raise ValueError(
                f"Cannot create sub-graph at depth {depth_val}, max is {max_subgraph_depth}"
            )
        instance = cls(
            id=id_,
            task_execution_id=task_execution_id,
            parent_graph_execution_id=parent_id,
            depth=depth_val,
            max_subgraph_depth=max_subgraph_depth,
        )
        return instance

    # --- Properties ---

    @property
    def task_execution_id(self) -> TaskExecutionId:
        return self._task_execution_id

    @property
    def parent_graph_execution_id(self) -> GraphExecutionId | None:
        return self._parent_graph_execution_id

    @property
    def depth(self) -> GraphDepth:
        return self._depth

    @property
    def max_subgraph_depth(self) -> MaxSubgraphDepth:
        return self._max_subgraph_depth

    @property
    def status(self) -> GraphExecutionStatus:
        return self._status

class InvalidGraphStateError(Exception):
    pass
