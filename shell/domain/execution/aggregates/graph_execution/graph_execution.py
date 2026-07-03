from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from shell.domain.execution.aggregates.graph_execution.exceptions.invalid_graph_state_error import (
    InvalidGraphStateError,
)
from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.value_objects.graph_definition_id import GraphDefinitionIdRef
from shell.domain.execution.value_objects.graph_depth import GraphDepth
from shell.domain.execution.value_objects.graph_execution_status import GraphExecutionStatus
from shell.domain.execution.value_objects.max_subgraph_depth import MaxSubgraphDepth
from shell.domain.platform.base.aggregate_root import AggregateRoot
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.state_data import StateData

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
        TaskExecutionId,
    )
    from shell.domain.execution.value_objects.goal import Goal
    from shell.domain.execution.value_objects.reason import Reason


from shell.domain.execution.aggregates.graph_execution.events.graph_execution_failed_event import (
            GraphExecutionFailedEvent,
        )
from shell.domain.execution.aggregates.graph_execution.events.graph_execution_completed_event import (
            GraphExecutionCompletedEvent,
        )
from shell.domain.execution.aggregates.graph_execution.events.graph_execution_sub_graph_spawn_requested_event import (
            GraphExecutionSubGraphSpawnRequestedEvent,
        )
from shell.domain.execution.aggregates.graph_execution.events.graph_execution_planned_event import (
            GraphExecutionPlannedEvent,
        )
from shell.domain.execution.aggregates.graph_execution.events.graph_execution_planning_started_event import (
            GraphExecutionPlanningStartedEvent,
        )
from shell.domain.execution.aggregates.graph_execution.events.graph_execution_created_event import (
            GraphExecutionCreatedEvent,
        )
from shell.domain.execution.aggregates.graph_execution.events.graph_execution_initialized_event import (
            GraphExecutionInitializedEvent,
        )
class GraphExecution(AggregateRoot[GraphExecutionId]):
    __slots__ = (
        "_task_execution_id",
        "_parent_graph_execution_id",
        "_depth",
        "_max_subgraph_depth",
        "_execution_status",
        "_graph_definition_id",
    )

    def __init__(
        self,
        id: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        depth: GraphDepth,
        max_subgraph_depth: MaxSubgraphDepth,
        parent_graph_execution_id: GraphExecutionId | None = None,
        graph_definition_id: GraphDefinitionIdRef | None = None,
    ) -> None:
        super().__init__(id)
        self._task_execution_id = task_execution_id
        self._parent_graph_execution_id = parent_graph_execution_id
        self._depth = depth
        self._max_subgraph_depth = max_subgraph_depth
        self._execution_status = GraphExecutionStatus.PENDING
        self._graph_definition_id = (
            graph_definition_id
            if graph_definition_id is not None
            else GraphDefinitionIdRef.generate()
        )

    @classmethod
    def restore(
        cls,
        id: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        depth: GraphDepth,
        max_subgraph_depth: MaxSubgraphDepth,
        parent_graph_execution_id: GraphExecutionId | None = None,
        graph_definition_id: GraphDefinitionIdRef | None = None,
    ) -> Self:
        return cls(
            id=id,
            task_execution_id=task_execution_id,
            parent_graph_execution_id=parent_graph_execution_id,
            depth=depth,
            max_subgraph_depth=max_subgraph_depth,
            graph_definition_id=graph_definition_id,
        )

    # --- Inicjalizacja ---

    @classmethod
    def initialize(
        cls,
        id_: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        graph_definition_id: GraphDefinitionIdRef,
        now: datetime,
    ) -> GraphExecution:
        instance = cls(
            id=id_,
            task_execution_id=task_execution_id,
            depth=GraphDepth(0),
            max_subgraph_depth=MaxSubgraphDepth(5),
            graph_definition_id=graph_definition_id,
        )

        instance.append_event(
            GraphExecutionInitializedEvent.now(
                graph_execution_id=id_,
                task_execution_id=task_execution_id,
                graph_definition_id=graph_definition_id,
                now=CreatedAt.from_datetime(now),
            )
        )
        return instance

    def emit_created_event(self, goal: Goal, now: datetime) -> None:
        if self._execution_status != GraphExecutionStatus.PENDING:
            raise InvalidGraphStateError(
                f"Cannot emit created event in status {self._execution_status}"
            )
        self.append_event(
            GraphExecutionCreatedEvent.now(
                graph_execution_id=self._id,
                task_execution_id=self._task_execution_id,
                now=CreatedAt.from_datetime(now),
                goal=goal,
                depth=self._depth,
            ),
        )

    # --- V3 FSM (execution status) ---

    def start_planning(self, now: datetime) -> None:
        if self._execution_status != GraphExecutionStatus.PENDING:
            raise InvalidGraphStateError(
                f"Cannot start planning in status {self._execution_status}"
            )
        self._execution_status = GraphExecutionStatus.PLANNING
        self.append_event(
            GraphExecutionPlanningStartedEvent.now(
                graph_execution_id=self._id,
                now=CreatedAt.from_datetime(now),
            )
        )

    def plan_complete(self, plan: StateData | dict[str, Any] | None, now: datetime) -> None:
        if self._execution_status != GraphExecutionStatus.PLANNING:
            raise InvalidGraphStateError(
                f"Cannot complete planning in status {self._execution_status}"
            )
        self._execution_status = GraphExecutionStatus.EXECUTING
        actual_plan = StateData(plan) if isinstance(plan, dict) else plan
        self.append_event(
            GraphExecutionPlannedEvent.now(
                graph_execution_id=self._id,
                now=CreatedAt.from_datetime(now),
                plan=actual_plan,
            )
        )

    def request_sub_graph_spawn(
        self,
        child_graph_execution_id: GraphExecutionId,
        graph_definition_id: GraphDefinitionIdRef,
        now: datetime,
        state_input: dict[str, Any] | None = None,
    ) -> None:
        if self._execution_status != GraphExecutionStatus.EXECUTING:
            raise InvalidGraphStateError(
                f"Cannot spawn sub-graph in status {self._execution_status}"
            )
        self.append_event(
            GraphExecutionSubGraphSpawnRequestedEvent.now(
                parent_graph_execution_id=self._id,
                child_graph_execution_id=child_graph_execution_id,
                graph_definition_id=graph_definition_id,
                now=CreatedAt.from_datetime(now),
                state_input=state_input,
            )
        )

    def complete(self, verifier_result: StateData | dict[str, Any] | None, now: datetime) -> None:
        if self._execution_status != GraphExecutionStatus.VERIFYING:
            raise InvalidGraphStateError(
                f"Cannot complete graph in status {self._execution_status}"
            )
        self._execution_status = GraphExecutionStatus.COMPLETED
        actual_result = (
            StateData(verifier_result) if isinstance(verifier_result, dict) else verifier_result
        )
        self.append_event(
            GraphExecutionCompletedEvent.now(
                graph_execution_id=self._id,
                now=CreatedAt.from_datetime(now),
                verifier_result=actual_result,
            )
        )

    def fail(self, reason: Reason, now: datetime) -> None:
        if self.execution_status not in (
            GraphExecutionStatus.PLANNING,
            GraphExecutionStatus.EXECUTING,
            GraphExecutionStatus.VERIFYING,
            GraphExecutionStatus.SUSPENDED,
        ):
            raise InvalidGraphStateError(f"Cannot fail graph in status {self._execution_status}")
        self._execution_status = GraphExecutionStatus.FAILED
        self.append_event(
            GraphExecutionFailedEvent.now(
                graph_execution_id=self._id,
                now=CreatedAt.from_datetime(now),
                reason=reason,
            )
        )

    def mark_verifying(self, now: datetime) -> None:
        if self._execution_status != GraphExecutionStatus.EXECUTING:
            raise InvalidGraphStateError(
                f"Cannot start verifying in status {self._execution_status}"
            )
        self._execution_status = GraphExecutionStatus.VERIFYING

    def suspend(self, now: datetime) -> None:
        if self._execution_status != GraphExecutionStatus.EXECUTING:
            raise InvalidGraphStateError(f"Cannot suspend graph in status {self._execution_status}")
        self._execution_status = GraphExecutionStatus.SUSPENDED

    def resume(self, now: datetime) -> None:
        if self._execution_status != GraphExecutionStatus.SUSPENDED:
            raise InvalidGraphStateError(f"Cannot resume graph in status {self._execution_status}")
        self._execution_status = GraphExecutionStatus.EXECUTING

    # --- Factory methods ---

    @classmethod
    def create_main_round(
        cls,
        id_: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        depth: GraphDepth,
        max_subgraph_depth: MaxSubgraphDepth,
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
        parent_depth: GraphDepth,
        max_subgraph_depth: MaxSubgraphDepth,
    ) -> GraphExecution:
        depth_val = GraphDepth(parent_depth.value + 1)
        if depth_val.value > max_subgraph_depth.value:
            raise ValueError(
                f"Cannot create sub-graph at depth {depth_val.value}, max is {max_subgraph_depth.value}"
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
    def execution_status(self) -> GraphExecutionStatus:
        return self._execution_status

    @property
    def status(self) -> GraphExecutionStatus:
        return self._execution_status

    @property
    def graph_definition_id(self) -> GraphDefinitionIdRef:
        return self._graph_definition_id

