from __future__ import annotations
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell_ddd.domain.events.events import DomainEvent
    from shell_ddd.domain.repositories.envelope_repository import EnvelopeArchive, EnvelopeRepository
    from shell_ddd.domain.repositories.node_result_repository import NodeResultRepository
    from shell_ddd.domain.repositories.prompt_repository import PromptRepository
    from shell_ddd.domain.repositories.rag_repository import RagDocumentRepository
    from shell_ddd.domain.repositories.runner_config_repository import RunnerConfigRepository
    from shell_ddd.domain.repositories.session_repository import SessionRepository
    from shell_ddd.domain.repositories.task_repository import TaskRepository
    from shell_ddd.domain.repositories.template_graph_repository import TemplateGraphRepository
    from shell_ddd.domain.repositories.workflow_repository import WorkflowRepository


class UnitOfWork(Protocol):
    tasks: TaskRepository
    workflows: WorkflowRepository
    envelopes: EnvelopeRepository
    prompts: PromptRepository
    node_results: NodeResultRepository
    runner_configs: RunnerConfigRepository
    envelope_archive: EnvelopeArchive
    rag_documents: RagDocumentRepository
    sessions: SessionRepository
    template_graphs: TemplateGraphRepository

    def stage_events(self, events: list[DomainEvent]) -> None: ...
    @property
    def events(self) -> list[DomainEvent]: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
    async def __aenter__(self) -> UnitOfWork: ...
    async def __aexit__(self, *args: object) -> None: ...
