from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.value_objects.graph_definition_id import GraphDefinitionIdRef
from shell.domain.execution.value_objects.graph_depth import GraphDepth
from shell.domain.execution.value_objects.graph_execution_initialization_status import (
    GraphExecutionInitializationStatus,
)
from shell.domain.execution.value_objects.graph_execution_status import GraphExecutionStatus
from shell.domain.execution.value_objects.graph_node_definition_execution_slot import (
    GraphNodeDefinitionExecutionSlot,
)
from shell.domain.execution.value_objects.max_subgraph_depth import MaxSubgraphDepth
from shell.domain.platform.base.aggregate_root import AggregateRoot
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.state_data import StateData

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
        GraphNodeExecutionId,
    )
    from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
        TaskExecutionId,
    )
    from shell.domain.execution.value_objects.graph_node_definition_id import GraphNodeDefinitionId
    from shell.domain.execution.value_objects.reason import Reason


class GraphExecution(AggregateRoot[GraphExecutionId]):
    __slots__ = (
        "_task_execution_id",
        "_parent_graph_execution_id",
        "_depth",
        "_max_subgraph_depth",
        "_execution_status",
        "_graph_definition_id",
        "_graph_node_definition_execution_slots",
        "_initialization_status",
    )

    def __init__(
        self,
        id: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        depth: GraphDepth,
        max_subgraph_depth: MaxSubgraphDepth,
        parent_graph_execution_id: GraphExecutionId | None = None,
        graph_definition_id: GraphDefinitionIdRef | None = None,
        initialization_status: GraphExecutionInitializationStatus | None = None,
        graph_node_definition_execution_slots: list[GraphNodeDefinitionExecutionSlot] | None = None,
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
        self._graph_node_definition_execution_slots = (
            graph_node_definition_execution_slots
            if graph_node_definition_execution_slots is not None
            else []
        )
        self._initialization_status = (
            initialization_status
            if initialization_status is not None
            else GraphExecutionInitializationStatus.PENDING
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
        initialization_status: GraphExecutionInitializationStatus | None = None,
        graph_node_definition_execution_slots: list[GraphNodeDefinitionExecutionSlot] | None = None,
    ) -> Self:
        return cls(
            id=id,
            task_execution_id=task_execution_id,
            parent_graph_execution_id=parent_graph_execution_id,
            depth=depth,
            max_subgraph_depth=max_subgraph_depth,
            graph_definition_id=graph_definition_id,
            initialization_status=initialization_status,
            graph_node_definition_execution_slots=graph_node_definition_execution_slots,
        )

    # --- Inicjalizacja ---

    @classmethod
    def initialize(
        cls,
        id_: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        graph_definition_id: GraphDefinitionIdRef,
        graph_node_definition_ids: list[GraphNodeDefinitionId],
        now: datetime,
    ) -> GraphExecution:
        instance = cls(
            id=id_,
            task_execution_id=task_execution_id,
            depth=GraphDepth(0),
            max_subgraph_depth=MaxSubgraphDepth(5),
        )
        instance._graph_definition_id = graph_definition_id
        instance._graph_node_definition_execution_slots = [
            GraphNodeDefinitionExecutionSlot(
                graph_node_definition_id=node_def_id,
            )
            for node_def_id in graph_node_definition_ids
        ]
        instance._initialization_status = GraphExecutionInitializationStatus.INITIALIZING

        from shell.domain.execution.aggregates.graph_execution.events.graph_execution_initialized_event import (
            GraphExecutionInitializedEvent,
        )

        instance.append_event(
            GraphExecutionInitializedEvent.now(
                graph_execution_id=id_,
                task_execution_id=task_execution_id,
                graph_definition_id=graph_definition_id,
                graph_node_definition_ids=graph_node_definition_ids,
                now=CreatedAt.from_datetime(now),
            )
        )
        return instance

    def prepare_node_definitions(
        self,
        graph_definition_id: GraphDefinitionIdRef,
        graph_node_definition_ids: list[GraphNodeDefinitionId],
    ) -> None:
        self._graph_definition_id = graph_definition_id
        self._graph_node_definition_execution_slots = [
            GraphNodeDefinitionExecutionSlot(graph_node_definition_id=node_def_id)
            for node_def_id in graph_node_definition_ids
        ]
        self._initialization_status = GraphExecutionInitializationStatus.INITIALIZING

    def attach_node_execution(
        self,
        node_definition_id: GraphNodeDefinitionId,
        node_execution_id: GraphNodeExecutionId,
        now: datetime,
    ) -> None:
        new_slots: list[GraphNodeDefinitionExecutionSlot] = []
        found = False
        for slot in self._graph_node_definition_execution_slots:
            if slot.graph_node_definition_id == node_definition_id:
                new_slots.append(slot.with_execution(node_execution_id))
                found = True
            else:
                new_slots.append(slot)

        if not found:
            raise UnknownNodeDefinitionError(f"Node definition {node_definition_id} not found")

        self._graph_node_definition_execution_slots = new_slots

        from shell.domain.execution.aggregates.graph_execution.events.graph_node_execution_attached_event import (
            GraphNodeExecutionAttachedEvent,
        )

        self.append_event(
            GraphNodeExecutionAttachedEvent.now(
                graph_execution_id=self._id,
                graph_node_definition_id=node_definition_id,
                graph_node_execution_id=node_execution_id,
                now=CreatedAt.from_datetime(now),
            )
        )

        if all(slot.is_filled for slot in self._graph_node_definition_execution_slots):
            self._initialization_status = GraphExecutionInitializationStatus.COMPLETED

            from shell.domain.execution.aggregates.graph_execution.events.graph_execution_ready_event import (
                GraphExecutionReadyEvent,
            )

            self.append_event(
                GraphExecutionReadyEvent.now(
                    graph_execution_id=self._id,
                    graph_node_definition_executions=[
                        slot
                        for slot in self._graph_node_definition_execution_slots
                        if slot.graph_node_execution_id is not None
                    ],
                    now=CreatedAt.from_datetime(now),
                )
            )

    def hold_initialization(self, now: datetime) -> None:
        if self._initialization_status != GraphExecutionInitializationStatus.INITIALIZING:
            raise InvalidInitializationStateError(
                f"Cannot hold in status {self._initialization_status}"
            )
        self._initialization_status = GraphExecutionInitializationStatus.HOLD

    def fail_initialization(self, now: datetime) -> None:
        if self._initialization_status not in (
            GraphExecutionInitializationStatus.INITIALIZING,
            GraphExecutionInitializationStatus.HOLD,
        ):
            raise InvalidInitializationStateError(
                f"Cannot fail in status {self._initialization_status}"
            )
        self._initialization_status = GraphExecutionInitializationStatus.FAILED
        self._execution_status = GraphExecutionStatus.FAILED

    # --- V3 FSM (execution status) ---

    def start_planning(self, now: datetime) -> None:
        if self._execution_status != GraphExecutionStatus.PENDING:
            raise InvalidGraphStateError(
                f"Cannot start planning in status {self._execution_status}"
            )
        self._execution_status = GraphExecutionStatus.PLANNING
        from shell.domain.execution.aggregates.graph_execution.events.graph_execution_planning_started_event import (
            GraphExecutionPlanningStartedEvent,
        )

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
        from shell.domain.execution.aggregates.graph_execution.events.graph_execution_planned_event import (
            GraphExecutionPlannedEvent,
        )

        actual_plan = StateData(plan) if isinstance(plan, dict) else plan
        self.append_event(
            GraphExecutionPlannedEvent.now(
                graph_execution_id=self._id,
                now=CreatedAt.from_datetime(now),
                plan=actual_plan,
            )
        )

    def complete(self, verifier_result: StateData | dict[str, Any] | None, now: datetime) -> None:
        if self._execution_status != GraphExecutionStatus.VERIFYING:
            raise InvalidGraphStateError(
                f"Cannot complete graph in status {self._execution_status}"
            )
        self._execution_status = GraphExecutionStatus.COMPLETED
        from shell.domain.execution.aggregates.graph_execution.events.graph_execution_completed_event import (
            GraphExecutionCompletedEvent,
        )

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
        from shell.domain.execution.aggregates.graph_execution.events.graph_execution_failed_event import (
            GraphExecutionFailedEvent,
        )

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

    @property
    def graph_node_definition_execution_slots(self) -> list[GraphNodeDefinitionExecutionSlot]:
        return list(self._graph_node_definition_execution_slots)

    @property
    def graph_node_definition_executions(self) -> dict[str, str]:
        return {
            slot.graph_node_definition_id.value: slot.graph_node_execution_id.value
            for slot in self._graph_node_definition_execution_slots
            if slot.graph_node_execution_id is not None
        }

    @property
    def initialization_status(self) -> GraphExecutionInitializationStatus:
        return self._initialization_status


class InvalidGraphStateError(Exception):
    pass


class UnknownNodeDefinitionError(Exception):
    pass


class InvalidInitializationStateError(Exception):
    pass
