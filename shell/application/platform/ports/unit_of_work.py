from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.definition.repositories.graph_definition_repository import (
        GraphDefinitionRepository,
    )
    from shell.domain.definition.repositories.rag_repository import RagDocumentRepository
    from shell.domain.definition.repositories.runner_config_repository import RunnerConfigRepository
    from shell.domain.execution.aggregates.envelope.ports import (
        EnvelopeArchive,
        EnvelopeRepository,
    )
    from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
        GraphExecutionRepository,
    )
    from shell.domain.execution.aggregates.graph_execution_state.repositories.graph_execution_state_repository import (
        GraphExecutionStateRepository,
    )
    from shell.domain.execution.aggregates.graph_node_execution.repositories.graph_node_execution_repository import (
        GraphNodeExecutionRepository,
    )
    from shell.domain.execution.aggregates.graph_node_execution_state.repositories.graph_node_execution_state_repository import (
        GraphNodeExecutionStateRepository,
    )
    from shell.domain.execution.aggregates.graph_node_transition_execution.repositories.graph_node_transition_execution_repository import (
        GraphNodeTransitionExecutionRepository,
    )
    from shell.domain.execution.aggregates.session.repositories.session_repository import SessionRepository
    from shell.domain.execution.aggregates.task_execution.repositories.task_execution_repository import (
        TaskExecutionRepository,
    )
    from shell.domain.execution.aggregates.task_execution_state.repositories.task_execution_state_repository import (
        TaskExecutionStateRepository,
    )
    from shell.domain.execution.aggregates.workflow.repositories.workflow_repository import (
        WorkflowRepository,
    )
    from shell.domain.platform.events import DomainEvent


class UnitOfWork(Protocol):
    @property
    def task_execution_repository(self) -> TaskExecutionRepository: ...

    @property
    def graph_execution_repository(self) -> GraphExecutionRepository: ...

    @property
    def workflow_repository(self) -> WorkflowRepository: ...

    @property
    def envelope_repository(self) -> EnvelopeRepository: ...

    @property
    def runner_config_repository(self) -> RunnerConfigRepository: ...

    @property
    def envelope_archive(self) -> EnvelopeArchive: ...

    @property
    def rag_document_repository(self) -> RagDocumentRepository: ...

    @property
    def session_repository(self) -> SessionRepository: ...

    @property
    def graph_definition_repository(self) -> GraphDefinitionRepository: ...

    @property
    def graph_execution_state_repository(self) -> GraphExecutionStateRepository: ...

    @property
    def task_execution_state_repository(self) -> TaskExecutionStateRepository: ...

    @property
    def graph_node_execution_repository(self) -> GraphNodeExecutionRepository: ...

    @property
    def graph_node_execution_state_repository(self) -> GraphNodeExecutionStateRepository: ...

    @property
    def graph_node_transition_execution_repository(self) -> GraphNodeTransitionExecutionRepository: ...

    def stage_events(self, events: list[DomainEvent]) -> None: ...

    @property
    def events(self) -> list[DomainEvent]: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...

    async def __aenter__(self) -> UnitOfWork: ...

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None: ...
