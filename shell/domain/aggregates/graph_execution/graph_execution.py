from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.entities.base import AggregateRoot
from shell.domain.entities.graph_node_execution import GraphNodeExecution
from shell.domain.events.events import GraphExecutionBuilt

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.entities.graph_definition import GraphDefinition
    from shell.domain.ports.identity import IdGenerator
    from shell.domain.value_objects.ids import (
        GraphDefinitionId,
        GraphExecutionId,
        TaskExecutionId,
    )


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
        id_gen: IdGenerator,
        now: datetime,
    ) -> GraphExecution:
        from shell.domain.value_objects.mode import Mode

        graph_node_executions: list[GraphNodeExecution] = []
        for graph_node_definition in graph_definition.graph_node_definitions:
            mode = (
                graph_node_definition.mode
                if isinstance(graph_node_definition.mode, Mode)
                else Mode(str(graph_node_definition.mode))
            )
            graph_node_executions.append(
                GraphNodeExecution(
                    id=id_gen.new_graph_node_execution_id(),
                    position=graph_node_definition.position,
                    node_dir="",
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
                    work_dir="",
                    status_initial=graph_node_definition.status_initial,
                    extra=dict(graph_node_definition.extra),
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
