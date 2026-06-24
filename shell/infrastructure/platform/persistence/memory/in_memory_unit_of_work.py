from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.platform.ports.unit_of_work import UnitOfWork
from shell.infrastructure.definition.persistence.memory.in_memory_graph_definition_repository import (
    InMemoryGraphDefinitionRepository,
)
from shell.infrastructure.definition.persistence.memory.in_memory_rag_document_repository import (
    InMemoryRagDocumentRepository,
)
from shell.infrastructure.definition.persistence.memory.in_memory_runner_config_repository import (
    InMemoryRunnerConfigRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_graph_execution_repository import (
    InMemoryGraphExecutionRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_graph_node_execution_repository import (
    InMemoryGraphNodeExecutionRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_session_repository import (
    InMemorySessionRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_task_execution_repository import (
    InMemoryTaskExecutionRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_task_execution_state_input_repository import (
    InMemoryTaskExecutionStateInputRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_workflow_repository import (
    InMemoryWorkflowRepository,
)
from shell.infrastructure.platform.persistence.memory.in_memory_graph_execution_state_input_repository import (
    InMemoryGraphExecutionStateInputRepository,
)
from shell.infrastructure.platform.persistence.memory.in_memory_graph_execution_state_output_repository import (
    InMemoryGraphExecutionStateOutputRepository,
)

if TYPE_CHECKING:
    from shell.domain.platform.events import DomainEvent


class InMemoryUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self._task_executions = InMemoryTaskExecutionRepository()
        self._task_execution_state_inputs = InMemoryTaskExecutionStateInputRepository()
        self._graph_node_executions = InMemoryGraphNodeExecutionRepository()
        self._graph_executions = InMemoryGraphExecutionRepository()
        self._graph_executions.link_task_executions(self._task_executions)
        self._graph_executions.link_graph_node_executions(self._graph_node_executions)
        self._workflows = InMemoryWorkflowRepository()
        self._runner_configs = InMemoryRunnerConfigRepository()
        self._rag_documents = InMemoryRagDocumentRepository()
        self._sessions = InMemorySessionRepository()
        self._graph_definitions = InMemoryGraphDefinitionRepository()
        self._graph_execution_state_inputs = InMemoryGraphExecutionStateInputRepository()
        self._graph_execution_state_outputs = InMemoryGraphExecutionStateOutputRepository()

        self._committed = False
        self._staged_events: list[DomainEvent] = []
        self._committed_events: list[DomainEvent] = []

    async def seed_base_planner(self) -> None:
        from shell.domain.definition.entities.graph_definition import GraphDefinition
        from shell.domain.definition.entities.graph_node_definition import GraphNodeDefinition
        from shell.domain.definition.value_objects.ids import (
            GraphDefinitionId,
            GraphNodeDefinitionId,
        )
        from shell.domain.platform.value_objects.mode import Mode

        await self._graph_definitions.save(
            GraphDefinition(
                id=GraphDefinitionId("base-planner-id"),
                name="base_planner",
                purpose="default_planning",
                graph_node_definitions=[
                    GraphNodeDefinition(
                        id=GraphNodeDefinitionId("base-planner-node-1"),
                        position=0,
                        mode=Mode("agent"),
                        role="agent",
                        node_type="agent",
                    ),
                ],
            )
        )

    @property
    def task_executions(self) -> InMemoryTaskExecutionRepository:
        return self._task_executions

    @property
    def task_execution_state_inputs(self) -> InMemoryTaskExecutionStateInputRepository:
        return self._task_execution_state_inputs

    @property
    def graph_executions(self) -> InMemoryGraphExecutionRepository:
        return self._graph_executions

    @property
    def workflows(self) -> InMemoryWorkflowRepository:
        return self._workflows

    @property
    @property
    def runner_configs(self) -> InMemoryRunnerConfigRepository:
        return self._runner_configs

    @property
    @property
    def rag_documents(self) -> InMemoryRagDocumentRepository:
        return self._rag_documents

    @property
    def sessions(self) -> InMemorySessionRepository:
        return self._sessions

    @property
    def graph_definitions(self) -> InMemoryGraphDefinitionRepository:
        return self._graph_definitions

    @property
    def graph_execution_state_inputs(self) -> InMemoryGraphExecutionStateInputRepository:
        return self._graph_execution_state_inputs

    @property
    def graph_execution_state_outputs(self) -> InMemoryGraphExecutionStateOutputRepository:
        return self._graph_execution_state_outputs

    @property
    def graph_node_executions(self) -> InMemoryGraphNodeExecutionRepository:
        return self._graph_node_executions

    def stage_events(self, events: list[DomainEvent]) -> None:
        self._staged_events.extend(events)

    @property
    def events(self) -> list[DomainEvent]:
        return list(self._staged_events)

    @property
    def committed_events(self) -> list[DomainEvent]:
        return list(self._committed_events)

    async def __aenter__(self) -> InMemoryUnitOfWork:
        self._committed = False
        self._staged_events = []
        self._committed_events = []
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

    async def commit(self) -> None:
        self._committed_events = list(self._staged_events)
        self._staged_events = []
        self._committed = True

    async def rollback(self) -> None:
        self._staged_events = []
        self._committed_events = []
        self._committed = False
