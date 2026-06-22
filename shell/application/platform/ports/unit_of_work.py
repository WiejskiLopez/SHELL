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
    from shell.domain.execution.aggregates.graph_execution.ports.graph_execution_repository import (
        GraphExecutionRepository,
    )
    from shell.domain.execution.aggregates.graph_execution_state_input.ports.graph_execution_state_input_repository import (
        GraphExecutionStateInputRepository,
    )
    from shell.domain.execution.aggregates.graph_execution_state_output.ports.graph_execution_state_output_repository import (
        GraphExecutionStateOutputRepository,
    )
    from shell.domain.execution.aggregates.graph_node_execution.ports.graph_node_execution_repository import (
        GraphNodeExecutionRepository,
    )
    from shell.domain.execution.aggregates.session.ports.session_repository import SessionRepository
    from shell.domain.execution.aggregates.task_execution.ports.task_execution_repository import (
        TaskExecutionRepository,
    )
    from shell.domain.execution.aggregates.task_execution_state_input.ports.task_execution_state_input_repository import (
        TaskExecutionStateInputRepository,
    )
    from shell.domain.execution.aggregates.workflow.ports.workflow_repository import (
        WorkflowRepository,
    )
    from shell.domain.platform.events import DomainEvent


class UnitOfWork(Protocol):
    @property
    def task_executions(self) -> TaskExecutionRepository: ...

    @property
    def task_execution_state_inputs(self) -> TaskExecutionStateInputRepository: ...

    @property
    def graph_executions(self) -> GraphExecutionRepository: ...

    @property
    def workflows(self) -> WorkflowRepository: ...

    @property
    def envelopes(self) -> EnvelopeRepository: ...

    @property
    def runner_configs(self) -> RunnerConfigRepository: ...

    @property
    def envelope_archive(self) -> EnvelopeArchive: ...

    @property
    def rag_documents(self) -> RagDocumentRepository: ...

    @property
    def sessions(self) -> SessionRepository: ...

    @property
    def graph_definitions(self) -> GraphDefinitionRepository: ...

    @property
    def graph_execution_state_inputs(self) -> GraphExecutionStateInputRepository: ...

    @property
    def graph_execution_state_outputs(self) -> GraphExecutionStateOutputRepository: ...

    @property
    def graph_node_executions(self) -> GraphNodeExecutionRepository: ...

    def stage_events(self, events: list[DomainEvent]) -> None: ...

    @property
    def events(self) -> list[DomainEvent]: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...

    async def __aenter__(self) -> UnitOfWork: ...

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None: ...
