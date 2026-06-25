from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.graph_execution.value_objects.spawning_request import (
    SpawningRequest,
)
from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import TaskExecutionId
from shell.domain.execution.value_objects.graph_depth import GraphDepth
from shell.domain.execution.value_objects.graph_execution_status import GraphExecutionStatus
from shell.domain.execution.value_objects.max_subgraph_depth import MaxSubgraphDepth
from shell.domain.execution.value_objects.reason import Reason
from shell.domain.platform.base.aggregate_root import AggregateRoot

from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.aggregates.graph_execution.entities.graph_execution_skill import (
        GraphExecutionSkill,
    )
    from shell.domain.execution.aggregates.graph_execution.entities.graph_execution_state_input import (
        GraphExecutionStateInput,
    )
    from shell.domain.execution.aggregates.graph_execution.entities.graph_execution_state_output import (
        GraphExecutionStateOutput,
    )
    from shell.domain.execution.value_objects.skill_payload import SkillPayload


class GraphExecution(AggregateRoot[GraphExecutionId]):
    __slots__ = (
        # V3 fields
        "_task_execution_id",
        "_parent_graph_execution_id",
        "_depth",
        "_max_subgraph_depth",
        "_status",
        "_skills",
        "_state_inputs",
        "_state_outputs",
        "_spawning_requests",
        # Legacy (deprecated)
        "_graph_definition_id",
        "_graph_node_execution_ids",
        "_transitions",
        "_loop_counters",
        "_state_input",
        "_state_output",
        "_timeout_at",
        "_correlation_id",
        "_tags",
    )

    def __init__(
        self,
        id: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        parent_graph_execution_id: GraphExecutionId | None = None,
        depth: int = 0,
        max_subgraph_depth: int = 5,
        # Legacy params
        graph_definition_id: str = "",
        graph_node_execution_ids: list[Any] | None = None,
        transitions: list[Any] | None = None,
        state_input: dict[str, Any] | None = None,
        state_output: dict[str, Any] | None = None,
        timeout_at: Any = None,
        correlation_id: str = "",
        tags: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(id)
        # V3
        self._task_execution_id = task_execution_id
        self._parent_graph_execution_id = parent_graph_execution_id
        self._depth = GraphDepth(depth)
        self._max_subgraph_depth = MaxSubgraphDepth(max_subgraph_depth)
        self._status = GraphExecutionStatus.PENDING
        self._skills = []
        self._state_inputs = []
        self._state_outputs = []
        self._spawning_requests: dict[str, SpawningRequest] = {}
        # Legacy
        self._graph_definition_id = graph_definition_id
        self._graph_node_execution_ids = _ensure_node_ids(graph_node_execution_ids) if graph_node_execution_ids else []
        self._transitions = list(transitions) if transitions else []
        self._loop_counters = {}
        self._state_input = state_input or {}
        self._state_output = state_output or {}
        self._timeout_at = timeout_at
        self._correlation_id = correlation_id
        self._tags = tags or {}

    @classmethod
    def restore(
        cls,
        id: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        parent_graph_execution_id: GraphExecutionId | None = None,
        depth: int = 0,
        max_subgraph_depth: int = 5,
        graph_definition_id: str = "",
        graph_node_execution_ids: list[Any] | None = None,
        transitions: list[Any] | None = None,
        state_input: dict[str, Any] | None = None,
        state_output: dict[str, Any] | None = None,
        timeout_at: Any = None,
        correlation_id: str = "",
        tags: dict[str, Any] | None = None,
    ) -> Self:
        return cls(
            id=id,
            task_execution_id=task_execution_id,
            parent_graph_execution_id=parent_graph_execution_id,
            depth=depth,
            max_subgraph_depth=max_subgraph_depth,
            graph_definition_id=graph_definition_id,
            graph_node_execution_ids=graph_node_execution_ids,
            transitions=transitions,
            state_input=state_input,
            state_output=state_output,
            timeout_at=timeout_at,
            correlation_id=correlation_id,
            tags=tags,
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

    def absorb_child_results(self, children_results: list[dict[str, Any]] | None, now: datetime) -> None:
        if self._status not in (GraphExecutionStatus.PLANNING, GraphExecutionStatus.EXECUTING):
            raise InvalidGraphStateError(
                f"Cannot absorb child results in status {self._status}"
            )
        if children_results:
            from shell.domain.execution.aggregates.graph_execution.entities.graph_execution_state_input import (
                GraphExecutionStateInput,
            )
            from shell.domain.execution.value_objects.ids import GraphExecutionStateInputId

            state = GraphExecutionStateInput(
                id=GraphExecutionStateInputId.generate(),
                graph_execution_id=self._id,
                payload={"children_results": children_results},
                created_at=now,
            )
            self._state_inputs.append(state)

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
        if self._status not in (GraphExecutionStatus.PLANNING, GraphExecutionStatus.EXECUTING, GraphExecutionStatus.SPAWNING, GraphExecutionStatus.READY, GraphExecutionStatus.VERIFYING):
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
        if self._status not in (GraphExecutionStatus.EXECUTING, GraphExecutionStatus.READY):
            raise InvalidGraphStateError(
                f"Cannot start verifying in status {self._status}"
            )
        self._status = GraphExecutionStatus.VERIFYING

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

    # --- Sub-graph spawning ---

    def request_sub_graph_spawn(
        self,
        child_graph_execution_id: GraphExecutionId,
        graph_definition_id: str,
        state_input: dict[str, Any] | None,
        correlation_id: str,
        expected_node_count: int,
        now: datetime,
    ) -> None:
        if self._status != GraphExecutionStatus.EXECUTING:
            raise InvalidGraphStateError(
                f"Cannot request sub-graph spawn in status {self._status}"
            )
        self._status = GraphExecutionStatus.SPAWNING
        request = SpawningRequest(
            child_graph_execution_id=child_graph_execution_id,
            expected_node_count=expected_node_count,
            initialized_node_count=0,
            definition_id=graph_definition_id,
            correlation_id=correlation_id,
        )
        self._spawning_requests[child_graph_execution_id.value] = request
        from shell.domain.execution.aggregates.graph_execution.events.graph_execution_sub_graph_spawn_requested_event import (
            GraphExecutionSubGraphSpawnRequestedEvent,
        )

        self.append_event(
            GraphExecutionSubGraphSpawnRequestedEvent.now(
                parent_graph_execution_id=self._id,
                child_graph_execution_id=child_graph_execution_id,
                graph_definition_id=graph_definition_id,
                now=now,
                state_input=state_input,
                correlation_id=correlation_id,
            )
        )

    def set_spawn_expected_node_count(
        self,
        child_graph_execution_id: GraphExecutionId,
        expected_node_count: int,
        now: datetime,
    ) -> None:
        request = self._spawning_requests.get(child_graph_execution_id.value)
        if request is None:
            return
        updated = SpawningRequest(
            child_graph_execution_id=request.child_graph_execution_id,
            expected_node_count=expected_node_count,
            initialized_node_count=0,
            definition_id=request.definition_id,
            correlation_id=request.correlation_id,
        )
        self._spawning_requests[child_graph_execution_id.value] = updated

    def confirm_node_initialized(
        self,
        child_graph_execution_id: GraphExecutionId,
        now: datetime,
    ) -> None:
        if self._status not in (GraphExecutionStatus.SPAWNING,):
            raise InvalidGraphStateError(
                f"Cannot confirm node initialized in status {self._status}"
            )
        request = self._spawning_requests.get(child_graph_execution_id.value)
        if request is None:
            return
        updated = SpawningRequest(
            child_graph_execution_id=request.child_graph_execution_id,
            expected_node_count=request.expected_node_count,
            initialized_node_count=request.initialized_node_count + 1,
            definition_id=request.definition_id,
            correlation_id=request.correlation_id,
        )
        self._spawning_requests[child_graph_execution_id.value] = updated
        if updated.expected_node_count < 1:
            return
        if updated.initialized_node_count >= updated.expected_node_count:
            self._spawning_requests.pop(child_graph_execution_id.value, None)
            self._status = GraphExecutionStatus.READY
            from shell.domain.execution.aggregates.graph_execution.events.graph_execution_ready_event import (
                GraphExecutionReadyEvent,
            )

            self.append_event(
                GraphExecutionReadyEvent.now(
                    graph_execution_id=self._id,
                    child_graph_execution_id=child_graph_execution_id,
                    now=now,
                )
            )

    def resume_from_ready(self, now: datetime) -> None:
        if self._status != GraphExecutionStatus.READY:
            raise InvalidGraphStateError(
                f"Cannot resume from ready in status {self._status}"
            )
        self._status = GraphExecutionStatus.EXECUTING

    # --- Skill management ---

    def add_skill(self, payload: SkillPayload, now: datetime) -> None:
        from shell.domain.execution.aggregates.graph_execution.entities.graph_execution_skill import (
            GraphExecutionSkill,
        )
        from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_skill_id import (
            GraphExecutionSkillId,
        )

        skill = GraphExecutionSkill(
            id=GraphExecutionSkillId.generate(),
            graph_execution_id=self._id,
            payload=payload,
            created_at=now,
        )
        self._skills.append(skill)

    # --- State I/O ---

    def add_state_input(self, payload: dict[str, Any], now: datetime) -> None:
        from shell.domain.execution.aggregates.graph_execution.entities.graph_execution_state_input import (
            GraphExecutionStateInput,
        )
        from shell.domain.execution.value_objects.ids import GraphExecutionStateInputId

        state = GraphExecutionStateInput(
            id=GraphExecutionStateInputId.generate(),
            graph_execution_id=self._id,
            payload=payload,
            created_at=now,
        )
        self._state_inputs.append(state)

    def add_state_output(self, payload: dict[str, Any], now: datetime) -> None:
        from shell.domain.execution.aggregates.graph_execution.entities.graph_execution_state_output import (
            GraphExecutionStateOutput,
        )
        from shell.domain.execution.value_objects.ids import GraphExecutionStateOutputId

        state = GraphExecutionStateOutput(
            id=GraphExecutionStateOutputId.generate(),
            graph_execution_id=self._id,
            payload=payload,
            created_at=now,
        )
        self._state_outputs.append(state)

    # --- Legacy methods (deprecated) ---

    def add_transition(self, transition: Any) -> None:
        self._transitions.append(transition)

    def add_graph_node_execution_id(self, node_id: Any) -> None:
        self._graph_node_execution_ids.append(node_id)

    def get_outgoing_transitions(self, source_node_execution_id: Any) -> tuple:
        from shell.domain.execution.aggregates.graph_execution.entities.graph_node_transition_execution import (
            GraphNodeTransitionExecution,
        )

        return tuple(
            sorted(
                (t for t in self._transitions if hasattr(t, 'source_node_execution_id') and t.source_node_execution_id == source_node_execution_id),
                key=lambda t: getattr(t, 'priority', 0),
            )
        )

    def get_incoming_transitions(self, target_node_execution_id: Any) -> tuple:
        return tuple(
            t for t in self._transitions
            if hasattr(t, 'target_node_execution_id') and t.target_node_execution_id == target_node_execution_id
        )

    def increment_loop_counter(self, transition_id: str, max_loop_count: int = 0) -> LoopCounter:
        from shell.domain.execution.aggregates.graph_execution.value_objects.loop_counter import (
            LoopCounter,
        )

        if transition_id not in self._loop_counters:
            self._loop_counters[transition_id] = LoopCounter(
                transition_id=transition_id,
                max_loop_count=max_loop_count,
            )
        counter = self._loop_counters[transition_id]
        incremented = counter.increment()
        self._loop_counters[transition_id] = incremented
        return incremented

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

    @property
    def spawning_requests(self) -> dict[str, SpawningRequest]:
        return dict(self._spawning_requests)

    @property
    def skills(self) -> tuple:
        return tuple(self._skills)

    @property
    def state_inputs(self) -> tuple:
        return tuple(self._state_inputs)

    @property
    def state_outputs(self) -> tuple:
        return tuple(self._state_outputs)

    # Legacy properties
    @property
    def state_input(self) -> dict[str, Any]:
        return dict(self._state_input)

    @property
    def state_output(self) -> dict[str, Any]:
        return dict(self._state_output)

    @property
    def graph_node_execution_ids(self) -> tuple:
        return tuple(self._graph_node_execution_ids)

    @property
    def graph_node_executions(self) -> tuple:
        from shell.domain.platform.value_objects.mode import Mode

        result: list[Any] = []
        for item in self._graph_node_execution_ids:
            from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
                GraphNodeExecution as GNE,
            )

            if isinstance(item, GraphNodeExecutionId):
                result.append(GNE(id=item, position=0, mode=Mode.WORKER, role="", node_type=""))
            else:
                result.append(item)
        return tuple(result)

    @property
    def transitions(self) -> tuple:
        return tuple(self._transitions)

    @property
    def loop_counters(self) -> dict[str, Any]:
        return dict(self._loop_counters)

    @property
    def graph_definition_id(self) -> str:
        return self._graph_definition_id

    @property
    def timeout_at(self) -> Timestamp | None:
        return self._timeout_at

    @property
    def correlation_id(self) -> str:
        return self._correlation_id

    @property
    def tags(self) -> dict[str, Any]:
        return dict(self._tags)


    # --- Legacy factory (deprecated) ---

    @classmethod
    def from_graph_definition(
        cls,
        *,
        id_: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        graph_definition: Any,
        node_ids: list[Any] | None = None,
        id_generator: Any = None,
        now: datetime,
        parent_graph_execution_id: GraphExecutionId | None = None,
        state_input: dict[str, Any] | None = None,
        correlation_id: str = "",
        depth: int = 0,
    ) -> GraphExecution:
        from shell.domain.execution.aggregates.graph_execution.value_objects.graph_node_transition_execution_id import (
            GraphNodeTransitionExecutionId,
        )
        from shell.domain.execution.aggregates.graph_execution.entities.graph_node_transition_execution import (
            GraphNodeTransitionExecution,
        )
        from shell.domain.execution.value_objects.edge_type import EdgeType

        graph_node_execution_ids: list[Any] = list(node_ids) if node_ids else []
        transitions: list[Any] = []

        if graph_node_execution_ids:
            sorted_ids = list(graph_node_execution_ids)
            for i in range(len(sorted_ids) - 1):
                transitions.append(
                    GraphNodeTransitionExecution(
                        id=GraphNodeTransitionExecutionId.generate(),
                        graph_execution_id=id_,
                        source_node_execution_id=sorted_ids[i],
                        target_node_execution_id=sorted_ids[i + 1],
                        transition_type=EdgeType.SEQUENCE,
                        priority=0,
                        label=f"sequence_{i}_to_{i + 1}",
                    )
                )

        graph_execution = cls(
            id=id_,
            task_execution_id=task_execution_id,
            parent_graph_execution_id=parent_graph_execution_id,
            depth=depth,
            graph_definition_id=getattr(graph_definition, 'id', ''),
            graph_node_execution_ids=graph_node_execution_ids,
            transitions=transitions,
            state_input=state_input,
            correlation_id=correlation_id,
        )

        return graph_execution


class InvalidGraphStateError(Exception):
    pass


def _ensure_node_ids(items: list[Any]) -> list[GraphNodeExecutionId]:
    result: list[GraphNodeExecutionId] = []
    for item in items:
        if isinstance(item, GraphNodeExecutionId):
            result.append(item)
        elif hasattr(item, "id") and isinstance(item.id, GraphNodeExecutionId):
            result.append(item.id)
        else:
            result.append(GraphNodeExecutionId(str(item)))
    return result
    pass
