from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.events.events import DomainEvent
    from shell.domain.repositories.envelope_repository import (
        EnvelopeArchive,
        EnvelopeRepository,
    )
    from shell.domain.repositories.graph_repository import GraphRepository
    from shell.domain.repositories.prompt_repository import PromptRepository
    from shell.domain.repositories.rag_repository import RagDocumentRepository
    from shell.domain.repositories.runner_config_repository import RunnerConfigRepository
    from shell.domain.repositories.session_repository import SessionRepository
    from shell.domain.repositories.task_repository import TaskRepository
    from shell.domain.repositories.template_graph_repository import TemplateGraphRepository
    from shell.domain.repositories.workflow_repository import WorkflowRepository


class UnitOfWork(Protocol):
    @property
    def tasks(self) -> TaskRepository: ...

    @property
    def graphs(self) -> GraphRepository: ...

    @property
    def workflows(self) -> WorkflowRepository: ...

    @property
    def envelopes(self) -> EnvelopeRepository: ...

    @property
    def prompts(self) -> PromptRepository: ...

    @property
    def runner_configs(self) -> RunnerConfigRepository: ...

    @property
    def envelope_archive(self) -> EnvelopeArchive: ...

    @property
    def rag_documents(self) -> RagDocumentRepository: ...

    @property
    def sessions(self) -> SessionRepository: ...

    @property
    def template_graphs(self) -> TemplateGraphRepository: ...

    def stage_events(self, events: list[DomainEvent]) -> None: ...

    @property
    def events(self) -> list[DomainEvent]: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...

    async def __aenter__(self) -> UnitOfWork: ...

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None: ...
