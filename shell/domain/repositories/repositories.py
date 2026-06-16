"""Repository port interfaces — re-exports from granular modules (backward compatibility)."""
from __future__ import annotations

from shell.domain.repositories.envelope_repository import EnvelopeArchive, EnvelopeRepository
from shell.domain.repositories.prompt_repository import PromptRepository
from shell.domain.repositories.rag_repository import RagDocumentRepository
from shell.domain.repositories.runner_config_repository import RunnerConfigRepository
from shell.domain.repositories.session_repository import SessionRepository
from shell.domain.repositories.task_repository import TaskRepository
from shell.domain.repositories.template_graph_repository import TemplateGraphRepository
from shell.domain.repositories.workflow_repository import WorkflowRepository

__all__ = [
    "EnvelopeArchive",
    "EnvelopeRepository",
    "PromptRepository",
    "RagDocumentRepository",
    "RunnerConfigRepository",
    "SessionRepository",
    "TaskRepository",
    "TemplateGraphRepository",
    "WorkflowRepository",
]
