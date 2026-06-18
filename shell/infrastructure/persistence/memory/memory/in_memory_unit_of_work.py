from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.ports.unit_of_work import UnitOfWork
from shell.domain.entities.graph_definition import GraphDefinition
from shell.domain.entities.graph_node_definition import GraphNodeDefinition
from shell.domain.value_objects.ids import (
    GraphDefinitionId,
    GraphNodeDefinitionId,
)
from shell.domain.value_objects.mode import Mode
from shell.infrastructure.persistence.memory.memory.in_memory_task_execution_repository import InMemoryTaskExecutionRepository
from shell.infrastructure.persistence.memory.memory.in_memory_graph_execution_repository import InMemoryGraphExecutionRepository
from shell.infrastructure.persistence.memory.memory.in_memory_workflow_repository import InMemoryWorkflowRepository
from shell.infrastructure.persistence.memory.memory.in_memory_envelope_repository import InMemoryEnvelopeRepository
from shell.infrastructure.persistence.memory.memory.in_memory_prompt_repository import InMemoryPromptRepository
from shell.infrastructure.persistence.memory.memory.in_memory_runner_config_repository import InMemoryRunnerConfigRepository
from shell.infrastructure.persistence.memory.memory.in_memory_envelope_archive import InMemoryEnvelopeArchive
from shell.infrastructure.persistence.memory.memory.in_memory_rag_document_repository import InMemoryRagDocumentRepository
from shell.infrastructure.persistence.memory.memory.in_memory_session_repository import InMemorySessionRepository
from shell.infrastructure.persistence.memory.memory.in_memory_graph_definition_repository import InMemoryGraphDefinitionRepository

if TYPE_CHECKING:
    from shell.domain.events.events import DomainEvent


class InMemoryUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self._task_executions = InMemoryTaskExecutionRepository()
        self._graph_executions = InMemoryGraphExecutionRepository()
        self._workflows = InMemoryWorkflowRepository()
        self._envelopes = InMemoryEnvelopeRepository()
        self._prompts = InMemoryPromptRepository()
        self._runner_configs = InMemoryRunnerConfigRepository()
        self._envelope_archive = InMemoryEnvelopeArchive()
        self._rag_documents = InMemoryRagDocumentRepository()
        self._sessions = InMemorySessionRepository()
        self._graph_definitions = InMemoryGraphDefinitionRepository()

        self._committed = False
        self._staged_events: list[DomainEvent] = []
        self._committed_events: list[DomainEvent] = []

    def seed_base_planner(self) -> None:
        self._graph_definitions._store["base_planner"] = GraphDefinition(
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

    @property
    def task_executions(self) -> InMemoryTaskExecutionRepository:
        return self._task_executions

    @property
    def graph_executions(self) -> InMemoryGraphExecutionRepository:
        return self._graph_executions

    @property
    def workflows(self) -> InMemoryWorkflowRepository:
        return self._workflows

    @property
    def envelopes(self) -> InMemoryEnvelopeRepository:
        return self._envelopes

    @property
    def prompts(self) -> InMemoryPromptRepository:
        return self._prompts

    @property
    def runner_configs(self) -> InMemoryRunnerConfigRepository:
        return self._runner_configs

    @property
    def envelope_archive(self) -> InMemoryEnvelopeArchive:
        return self._envelope_archive

    @property
    def rag_documents(self) -> InMemoryRagDocumentRepository:
        return self._rag_documents

    @property
    def sessions(self) -> InMemorySessionRepository:
        return self._sessions

    @property
    def graph_definitions(self) -> InMemoryGraphDefinitionRepository:
        return self._graph_definitions

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

    async def commit(self) -> None:
        self._committed_events = list(self._staged_events)
        self._staged_events = []
        self._committed = True

    async def rollback(self) -> None:
        self._staged_events = []
        self._committed_events = []
        self._committed = False
