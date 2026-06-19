from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.graph_execution.join_counter import JoinCounter
from shell.domain.execution.aggregates.graph_execution.loop_counter import LoopCounter
from shell.domain.execution.aggregates.graph_execution.parallel_group import ParallelGroup
from shell.domain.execution.entities.graph_node_execution import GraphNodeExecution
from shell.domain.execution.entities.graph_node_transition_execution import (
    GraphNodeTransitionExecution,
)
from shell.domain.execution.events import GraphExecutionBuiltEvent
from shell.domain.platform.base import AggregateRoot
from shell.domain.platform.value_objects.transition_type import TransitionType

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.definition.entities.graph_definition import GraphDefinition
    from shell.domain.platform.ports.identity import IdGenerator
    from shell.domain.definition.value_objects.ids import (
    GraphDefinitionId
)
from shell.domain.execution.value_objects.ids import (
    GraphExecutionId,
    GraphNodeExecutionId,
    TaskExecutionId
)


class GraphExecution(AggregateRoot["GraphExecutionId"]):
    """Graph aggregate root — owns its GraphNodeExecutions and GraphNodeTransitionExecutions."""

    __slots__ = (
        "_task_execution_id",
        "_graph_definition_id",
        "_parent_graph_execution_id",
        "_parent_tasker_node_execution_id",
        "_state_input",
        "_state_output",
        "_depth",
        "_timeout_at",
        "_correlation_id",
        "_tags",
        "_graph_node_executions",
        "_transitions",
        "_parallel_groups",
        "_join_counters",
        "_loop_counters",
    )

    _task_execution_id: TaskExecutionId
    _graph_definition_id: GraphDefinitionId
    _parent_graph_execution_id: GraphExecutionId | None
    _parent_tasker_node_execution_id: GraphNodeExecutionId | None
    _state_input: dict[str, Any]
    _state_output: dict[str, Any]
    _depth: int
    _timeout_at: datetime | None
    _correlation_id: str
    _tags: dict[str, Any]
    _graph_node_executions: list[GraphNodeExecution]
    _transitions: list[GraphNodeTransitionExecution]
    _parallel_groups: dict[str, ParallelGroup]
    _join_counters: dict[str, JoinCounter]
    _loop_counters: dict[str, LoopCounter]

    def __init__(
        self,
        id: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        graph_definition_id: GraphDefinitionId,
        graph_node_executions: list[GraphNodeExecution] | None = None,
        transitions: list[GraphNodeTransitionExecution] | None = None,
        parent_graph_execution_id: GraphExecutionId | None = None,
        parent_tasker_node_execution_id: GraphNodeExecutionId | None = None,
        state_input: dict[str, Any] | None = None,
        state_output: dict[str, Any] | None = None,
        depth: int = 0,
        timeout_at: datetime | None = None,
        correlation_id: str = "",
        tags: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(id)
        self._task_execution_id = task_execution_id
        self._graph_definition_id = graph_definition_id
        self._parent_graph_execution_id = parent_graph_execution_id
        self._parent_tasker_node_execution_id = parent_tasker_node_execution_id
        self._state_input = state_input or {}
        self._state_output = state_output or {}
        self._depth = depth
        self._timeout_at = timeout_at
        self._correlation_id = correlation_id
        self._tags = tags or {}
        self._graph_node_executions = list(graph_node_executions) if graph_node_executions else []
        self._transitions = list(transitions) if transitions else []
        self._parallel_groups = {}
        self._join_counters = {}
        self._loop_counters = {}

    @property
    def task_execution_id(self) -> TaskExecutionId:
        return self._task_execution_id

    @property
    def graph_definition_id(self) -> GraphDefinitionId:
        return self._graph_definition_id

    @property
    def parent_graph_execution_id(self) -> GraphExecutionId | None:
        return self._parent_graph_execution_id

    @property
    def parent_tasker_node_execution_id(self) -> GraphNodeExecutionId | None:
        return self._parent_tasker_node_execution_id

    @property
    def state_input(self) -> dict[str, Any]:
        return self._state_input

    @property
    def state_output(self) -> dict[str, Any]:
        return self._state_output

    @state_output.setter
    def state_output(self, value: dict[str, Any]) -> None:
        self._state_output = value

    @property
    def depth(self) -> int:
        return self._depth

    @property
    def timeout_at(self) -> datetime | None:
        return self._timeout_at

    @property
    def correlation_id(self) -> str:
        return self._correlation_id

    @property
    def tags(self) -> dict[str, Any]:
        return self._tags

    @property
    def graph_node_executions(self) -> tuple[GraphNodeExecution, ...]:
        return tuple(self._graph_node_executions)

    @property
    def transitions(self) -> tuple[GraphNodeTransitionExecution, ...]:
        return tuple(self._transitions)

    def get_outgoing_transitions(
        self, source_node_execution_id: GraphNodeExecutionId
    ) -> tuple[GraphNodeTransitionExecution, ...]:
        return tuple(
            sorted(
                (
                    t
                    for t in self._transitions
                    if t.source_node_execution_id == source_node_execution_id
                ),
                key=lambda t: t.priority,
            )
        )

    def get_incoming_transitions(
        self, target_node_execution_id: GraphNodeExecutionId
    ) -> tuple[GraphNodeTransitionExecution, ...]:
        return tuple(
            t for t in self._transitions if t.target_node_execution_id == target_node_execution_id
        )

    def add_transition(self, transition: GraphNodeTransitionExecution) -> None:
        self._transitions.append(transition)

    @classmethod
    def from_graph_definition(
        cls,
        *,
        id_: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        graph_definition: GraphDefinition,
        id_gen: IdGenerator,
        now: datetime,
        parent_graph_execution_id: GraphExecutionId | None = None,
        parent_tasker_node_execution_id: GraphNodeExecutionId | None = None,
        state_input: dict[str, Any] | None = None,
        correlation_id: str = "",
        depth: int = 0,
    ) -> GraphExecution:
        from shell.domain.platform.value_objects.mode import Mode

        graph_node_executions: list[GraphNodeExecution] = []
        previous_node_id: GraphNodeExecutionId | None = None

        for graph_node_definition in graph_definition.graph_node_definitions:
            mode = (
                graph_node_definition.mode
                if isinstance(graph_node_definition.mode, Mode)
                else Mode(str(graph_node_definition.mode))
            )
            node_id = id_gen.new_graph_node_execution_id()
            graph_node_executions.append(
                GraphNodeExecution(
                    id=node_id,
                    position=graph_node_definition.position,
                    mode=mode,
                    role=graph_node_definition.role,
                    node_type=graph_node_definition.node_type,
                    model=graph_node_definition.model,
                    command=graph_node_definition.command,
                    timeout=graph_node_definition.timeout,
                    retries=graph_node_definition.retries,
                    log_level=graph_node_definition.log_level,
                    max_step=graph_node_definition.max_step or 0,
                    no_ask_user=graph_node_definition.no_ask_user,
                    autopilot=graph_node_definition.autopilot,
                    task_execution_id="",
                    source_dir="",
                    status_initial=graph_node_definition.status_initial,
                    extra=dict(graph_node_definition.extra),
                    sub_graph_definition_id=graph_node_definition.extra.get("sub_graph_definition_id"),
                    timeout_seconds=graph_node_definition.timeout,
                    max_retries=graph_node_definition.retries,
                )
            )
            previous_node_id = node_id

        graph_execution = cls(
            id=id_,
            task_execution_id=task_execution_id,
            graph_definition_id=graph_definition.id,
            graph_node_executions=graph_node_executions,
            parent_graph_execution_id=parent_graph_execution_id,
            parent_tasker_node_execution_id=parent_tasker_node_execution_id,
            state_input=state_input,
            depth=depth,
            correlation_id=correlation_id,
        )

        graph_execution._build_sequence_transitions(previous_node_id)
        graph_execution.append_event(
            GraphExecutionBuiltEvent.now(
                graph_execution_id=id_,
                task_execution_id=task_execution_id,
                graph_definition_id=graph_definition.id,
                now=now,
            )
        )
        return graph_execution

    def _build_sequence_transitions(
        self, last_node_id: GraphNodeExecutionId | None
    ) -> None:
        from shell.domain.execution.value_objects.ids import GraphNodeTransitionExecutionId

        sorted_nodes = sorted(self._graph_node_executions, key=lambda n: n.position)
        for i in range(len(sorted_nodes) - 1):
            self._transitions.append(
                GraphNodeTransitionExecution(
                    id=GraphNodeTransitionExecutionId.generate(),
                    graph_execution_id=self.id,
                    source_node_execution_id=sorted_nodes[i].id,
                    target_node_execution_id=sorted_nodes[i + 1].id,
                    transition_type=TransitionType.SEQUENCE,
                    priority=0,
                    label=f"sequence_{sorted_nodes[i].position}_to_{sorted_nodes[i + 1].position}",
                )
            )

    def add_graph_node_execution(self, graph_node_execution: GraphNodeExecution) -> None:
        self._graph_node_executions.append(graph_node_execution)

    # ── Parallel group management ─────────────────────────────────────────

    @property
    def parallel_groups(self) -> dict[str, ParallelGroup]:
        return dict(self._parallel_groups)

    def create_parallel_group(
        self,
        group_id: str,
        fork_node_execution_id: GraphNodeExecutionId,
        target_node_ids: list[GraphNodeExecutionId],
    ) -> ParallelGroup:
        group = ParallelGroup(
            group_id=group_id,
            fork_node_execution_id=fork_node_execution_id,
            pending_node_ids={nid.value for nid in target_node_ids},
        )
        self._parallel_groups[group_id] = group
        return group

    def complete_parallel_node(self, group_id: str, node_id: str) -> ParallelGroup | None:
        group = self._parallel_groups.get(group_id)
        if group is not None:
            group.mark_completed(node_id)
            if group.is_complete:
                self._parallel_groups.pop(group_id, None)
        return group

    def is_node_in_any_parallel_group(self, node_id: str) -> bool:
        return any(
            node_id in group.pending_node_ids or node_id in group.completed_node_ids
            for group in self._parallel_groups.values()
        )

    def get_parallel_group_for_node(self, node_id: str) -> ParallelGroup | None:
        for group in self._parallel_groups.values():
            if node_id in group.pending_node_ids or node_id in group.completed_node_ids:
                return group
        return None

    # ── Join counter management ───────────────────────────────────────────

    @property
    def join_counters(self) -> dict[str, JoinCounter]:
        return dict(self._join_counters)

    def create_join_counter(
        self,
        transition_id: str,
        target_node_execution_id: GraphNodeExecutionId,
        wait_count: int,
    ) -> JoinCounter:
        counter = JoinCounter(
            transition_id=transition_id,
            target_node_execution_id=target_node_execution_id,
            wait_count=wait_count,
        )
        self._join_counters[transition_id] = counter
        return counter

    def record_join_completion(
        self, transition_id: str, source_node_id: str
    ) -> JoinCounter | None:
        counter = self._join_counters.get(transition_id)
        if counter is not None and counter.record_completion(source_node_id):
            return counter
        return None

    # ── Loop counter management ───────────────────────────────────────────

    @property
    def loop_counters(self) -> dict[str, LoopCounter]:
        return dict(self._loop_counters)

    def get_or_create_loop_counter(
        self, transition_id: str, max_loop_count: int
    ) -> LoopCounter:
        if transition_id not in self._loop_counters:
            self._loop_counters[transition_id] = LoopCounter(
                transition_id=transition_id,
                max_loop_count=max_loop_count,
            )
        return self._loop_counters[transition_id]
