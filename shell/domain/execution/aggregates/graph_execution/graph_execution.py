from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.graph_execution.entities.graph_node_transition_execution import (
    GraphNodeTransitionExecution,
)
from shell.domain.execution.aggregates.graph_execution.events.graph_execution_built_event import (
    GraphExecutionBuiltEvent,
)
from shell.domain.execution.aggregates.graph_execution.value_objects.loop_counter import LoopCounter
from shell.domain.execution.value_objects.graph_execution_definition import (
    GraphExecutionDefinition,  # noqa: TC002 — GraphExecutionDefinition używany w metodzie from_graph_definition() GraphExecution
)
from shell.domain.platform.base import AggregateRoot
from shell.domain.platform.value_objects.transition_type import TransitionType

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.platform.ports.identity import IdGenerator
from shell.domain.execution.aggregates.graph_execution.graph_execution_id import (
    GraphExecutionId,  # noqa: TC002 — GraphExecutionId używany w konstruktorze i typach propertisów GraphExecution
)
from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.execution.aggregates.task_execution.task_execution_id import (
    TaskExecutionId,  # noqa: TC002 — TaskExecutionId używany w konstruktorze i typach propertisów GraphExecution
)


class GraphExecution(AggregateRoot["GraphExecutionId"]):
    """Graph aggregate root — owns transitions, loop counters, references node IDs."""

    __slots__ = (
        "_task_execution_id",
        "_graph_definition_id",
        "_parent_graph_execution_id",
        "_state_input",
        "_state_output",
        "_depth",
        "_timeout_at",
        "_correlation_id",
        "_tags",
        "_graph_node_execution_ids",
        "_graph_node_execution_objects",
        "_transitions",
        "_loop_counters",
    )

    _task_execution_id: TaskExecutionId
    _graph_definition_id: str
    _parent_graph_execution_id: GraphExecutionId | None
    _state_input: dict[str, Any]
    _state_output: dict[str, Any]
    _depth: int
    _timeout_at: datetime | None
    _correlation_id: str
    _tags: dict[str, Any]
    _graph_node_execution_ids: list[GraphNodeExecutionId]
    _graph_node_execution_objects: list[Any]
    _transitions: list[GraphNodeTransitionExecution]
    _loop_counters: dict[str, LoopCounter]

    def __init__(
        self,
        id: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        graph_definition_id: str,
        graph_node_execution_ids: list[GraphNodeExecutionId] | None = None,
        graph_node_executions: Any = None,
        transitions: list[GraphNodeTransitionExecution] | None = None,
        parent_graph_execution_id: GraphExecutionId | None = None,
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
        self._state_input = state_input or {}
        self._state_output = state_output or {}
        self._depth = depth
        self._timeout_at = timeout_at
        self._correlation_id = correlation_id
        self._tags = tags or {}
        combined_nodes = graph_node_execution_ids or graph_node_executions or []
        self._graph_node_execution_ids = _ensure_node_ids(combined_nodes)
        self._graph_node_execution_objects = [
            n for n in combined_nodes if not isinstance(n, (GraphNodeExecutionId, str))
        ]
        self._transitions = list(transitions) if transitions else []
        self._loop_counters = {}

    @property
    def task_execution_id(self) -> TaskExecutionId:
        return self._task_execution_id

    @property
    def graph_definition_id(self) -> str:
        return self._graph_definition_id

    @property
    def parent_graph_execution_id(self) -> GraphExecutionId | None:
        return self._parent_graph_execution_id

    @property
    def state_input(self) -> dict[str, Any]:
        return dict(self._state_input)

    @property
    def state_output(self) -> dict[str, Any]:
        return dict(self._state_output)

    def absorb_child_results(self, value: dict[str, Any]) -> None:
        self._state_output = dict(value) if value else {}

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
        return dict(self._tags)

    @property
    def graph_node_execution_ids(self) -> tuple[GraphNodeExecutionId, ...]:
        return tuple(self._graph_node_execution_ids)

    @property
    def graph_node_executions(self) -> tuple[Any, ...]:
        if self._graph_node_execution_objects:
            return tuple(self._graph_node_execution_objects)
        from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
            GraphNodeExecution as GNE,
        )

        result: list[Any] = []
        for nid in self._graph_node_execution_ids:
            if isinstance(nid, GraphNodeExecutionId):
                result.append(GNE(id=nid, position=0, mode=None, role="", node_type=""))
            else:
                result.append(nid)
        return tuple(result)

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

    def add_graph_node_execution_id(self, node_id: GraphNodeExecutionId) -> None:
        self._graph_node_execution_ids.append(node_id)

    @classmethod
    def from_graph_definition(
        cls,
        *,
        id_: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        graph_definition: GraphExecutionDefinition,
        node_ids: list[GraphNodeExecutionId] | None = None,
        id_gen: IdGenerator,
        now: datetime,
        parent_graph_execution_id: GraphExecutionId | None = None,
        state_input: dict[str, Any] | None = None,
        correlation_id: str = "",
        depth: int = 0,
    ) -> GraphExecution:
        from shell.domain.execution.aggregates.graph_execution.value_objects.ids.graph_node_transition_execution_id import (
            GraphNodeTransitionExecutionId,
        )

        graph_node_execution_ids: list[GraphNodeExecutionId] = list(node_ids) if node_ids else []
        transitions: list[GraphNodeTransitionExecution] = []

        if graph_node_execution_ids:
            sorted_ids = list(graph_node_execution_ids)
            for i in range(len(sorted_ids) - 1):
                transitions.append(
                    GraphNodeTransitionExecution(
                        id=GraphNodeTransitionExecutionId.generate(),
                        graph_execution_id=id_,
                        source_node_execution_id=sorted_ids[i],
                        target_node_execution_id=sorted_ids[i + 1],
                        transition_type=TransitionType.SEQUENCE,
                        priority=0,
                        label=f"sequence_{i}_to_{i + 1}",
                    )
                )

        graph_execution = cls(
            id=id_,
            task_execution_id=task_execution_id,
            graph_definition_id=graph_definition.id,
            graph_node_execution_ids=graph_node_execution_ids,
            transitions=transitions,
            parent_graph_execution_id=parent_graph_execution_id,
            state_input=state_input,
            depth=depth,
            correlation_id=correlation_id,
        )

        graph_execution.append_event(
            GraphExecutionBuiltEvent.now(
                graph_execution_id=id_,
                task_execution_id=task_execution_id,
                graph_definition_id=graph_definition.id,
                now=now,
            )
        )
        return graph_execution

    # ── Loop counter management ───────────────────────────────────────────

    @property
    def loop_counters(self) -> dict[str, LoopCounter]:
        return dict(self._loop_counters)

    def get_or_create_loop_counter(self, transition_id: str, max_loop_count: int) -> LoopCounter:
        if transition_id not in self._loop_counters:
            self._loop_counters[transition_id] = LoopCounter(
                transition_id=transition_id,
                max_loop_count=max_loop_count,
            )
        return self._loop_counters[transition_id]


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
