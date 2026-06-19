from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.entities.base import AggregateRoot
from shell.domain.entities.graph_node_execution import GraphNodeExecution
from shell.domain.entities.graph_node_transition import GraphNodeTransition
from shell.domain.events.events import GraphExecutionBuilt
from shell.domain.value_objects.transition_type import TransitionType

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.entities.graph_definition import GraphDefinition
    from shell.domain.ports.identity import IdGenerator
    from shell.domain.value_objects.ids import (
        GraphDefinitionId,
        GraphExecutionId,
        GraphNodeExecutionId,
        GraphNodeTransitionId,
        TaskExecutionId,
    )


class GraphExecution(AggregateRoot["GraphExecutionId"]):
    """Graph aggregate root — owns its GraphNodeExecutions and GraphNodeTransitions."""

    __slots__ = (
        "_task_execution_id",
        "_graph_definition_id",
        "_graph_node_executions",
        "_transitions",
    )

    _task_execution_id: TaskExecutionId
    _graph_definition_id: GraphDefinitionId
    _graph_node_executions: list[GraphNodeExecution]
    _transitions: list[GraphNodeTransition]

    def __init__(
        self,
        id: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        graph_definition_id: GraphDefinitionId,
        graph_node_executions: list[GraphNodeExecution] | None = None,
        transitions: list[GraphNodeTransition] | None = None,
    ) -> None:
        super().__init__(id)
        self._task_execution_id = task_execution_id
        self._graph_definition_id = graph_definition_id
        self._graph_node_executions = list(graph_node_executions) if graph_node_executions else []
        self._transitions = list(transitions) if transitions else []

    @property
    def task_execution_id(self) -> TaskExecutionId:
        return self._task_execution_id

    @property
    def graph_definition_id(self) -> GraphDefinitionId:
        return self._graph_definition_id

    @property
    def graph_node_executions(self) -> tuple[GraphNodeExecution, ...]:
        return tuple(self._graph_node_executions)

    @property
    def transitions(self) -> tuple[GraphNodeTransition, ...]:
        return tuple(self._transitions)

    def get_outgoing_transitions(
        self, source_node_execution_id: GraphNodeExecutionId
    ) -> tuple[GraphNodeTransition, ...]:
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
    ) -> tuple[GraphNodeTransition, ...]:
        return tuple(
            t for t in self._transitions if t.target_node_execution_id == target_node_execution_id
        )

    def add_transition(self, transition: GraphNodeTransition) -> None:
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
    ) -> GraphExecution:
        from shell.domain.entities.graph_node_transition import GraphNodeTransition
        from shell.domain.value_objects.ids import GraphNodeTransitionId
        from shell.domain.value_objects.mode import Mode

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
                )
            )
            previous_node_id = node_id

        graph_execution = cls(
            id=id_,
            task_execution_id=task_execution_id,
            graph_definition_id=graph_definition.id,
            graph_node_executions=graph_node_executions,
        )

        graph_execution._build_sequence_transitions(previous_node_id)
        graph_execution.append_event(
            GraphExecutionBuilt.now(
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
        from shell.domain.value_objects.ids import GraphNodeTransitionId

        sorted_nodes = sorted(self._graph_node_executions, key=lambda n: n.position)
        for i in range(len(sorted_nodes) - 1):
            self._transitions.append(
                GraphNodeTransition(
                    id=GraphNodeTransitionId.generate(),
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
