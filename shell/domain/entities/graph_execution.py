"""Graph aggregate root.

A Graph is the concrete realisation of a workflow plan for a specific task_execution.
It is built from a GraphDefinition in reaction to the ``TaskExecutionCreated`` event
(see ``BuildGraphExecutionOnTaskExecutionCreated`` event handler) — a Task does not know
which Graph realises it; the Graph holds the back-reference (``task_execution_id``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from shell.domain.entities.base import AggregateRoot
from shell.domain.entities.graph_node_execution import GraphNodeExecution
from shell.domain.events.events import GraphExecutionBuilt

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.entities.graph_definition import GraphDefinition
    from shell.domain.value_objects.ids import (
        GraphDefinitionId,
        GraphExecutionId,
        GraphNodeExecutionId,
        TaskExecutionId,
    )


class _GraphNodeExecutionIdFactory(Protocol):
    """Structural type for a callable that produces a fresh GraphNodeExecutionId."""

    def __call__(self) -> GraphNodeExecutionId: ...


class GraphExecution(AggregateRoot["GraphExecutionId"]):
    """Graph aggregate root — owns its GraphNodeExecutions."""

    __slots__ = (
        "_task_execution_id",
        "_graph_definition_id",
        "_graph_node_executions",
    )

    _task_execution_id: TaskExecutionId
    _graph_definition_id: GraphDefinitionId
    _graph_node_executions: list[GraphNodeExecution]

    def __init__(
        self,
        id: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        graph_definition_id: GraphDefinitionId,
        graph_node_executions: list[GraphNodeExecution] | None = None,
    ) -> None:
        super().__init__(id)
        self._task_execution_id = task_execution_id
        self._graph_definition_id = graph_definition_id
        self._graph_node_executions = list(graph_node_executions) if graph_node_executions else []

    @property
    def task_execution_id(self) -> TaskExecutionId:
        return self._task_execution_id

    @property
    def graph_definition_id(self) -> GraphDefinitionId:
        return self._graph_definition_id

    @property
    def graph_node_executions(self) -> list[GraphNodeExecution]:
        return self._graph_node_executions

    @classmethod
    def from_graph_definition(
        cls,
        *,
        id_: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        graph_definition: GraphDefinition,
        graph_node_execution_id_factory: _GraphNodeExecutionIdFactory,
        now: datetime,
    ) -> GraphExecution:
        """Build a Graph from a GraphDefinition snapshot. Emits GraphExecutionBuilt."""
        from shell.domain.value_objects.mode import Mode

        graph_node_executions: list[GraphNodeExecution] = []
        for tn in graph_definition.graph_node_definitions:
            mode = tn.mode if isinstance(tn.mode, Mode) else Mode(str(tn.mode))
            graph_node_executions.append(
                GraphNodeExecution(
                    id=graph_node_execution_id_factory(),
                    position=tn.position,
                    node_dir="",
                    mode=mode,
                    role=tn.role,
                    node_type=tn.node_type,
                    model=tn.model,
                    command=tn.command,
                    timeout=tn.timeout,
                    retries=tn.retries,
                    log_level=tn.log_level,
                    max_step=tn.max_step or 0,
                    no_ask_user=tn.no_ask_user,
                    autopilot=tn.autopilot,
                    task_execution_id="",
                    source_dir="",
                    work_dir="",
                    status_initial=tn.status_initial,
                    extra=dict(tn.extra),
                )
            )
        graph_execution = cls(
            id=id_,
            task_execution_id=task_execution_id,
            graph_definition_id=graph_definition.id,
            graph_node_executions=graph_node_executions,
        )
        graph_execution.append_event(
            GraphExecutionBuilt.now(
                graph_execution_id=id_,
                task_execution_id=task_execution_id,
                graph_definition_id=graph_definition.id,
                now=now,
            )
        )
        return graph_execution

    def add_graph_node_execution(self, graph_node_execution: GraphNodeExecution) -> None:
        self._graph_node_executions.append(graph_node_execution)
