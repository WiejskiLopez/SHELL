"""Repository port interfaces — re-exports from granular modules (backward compatibility)."""
from __future__ import annotations

from shell_ddd.domain.repositories.envelope_repository import EnvelopeArchive, EnvelopeRepository
from shell_ddd.domain.repositories.node_result_repository import NodeResultRepository
from shell_ddd.domain.repositories.prompt_repository import PromptRepository
from shell_ddd.domain.repositories.rag_repository import RagDocumentRepository
from shell_ddd.domain.repositories.runner_config_repository import RunnerConfigRepository
from shell_ddd.domain.repositories.session_repository import SessionRepository
from shell_ddd.domain.repositories.task_repository import TaskRepository
from shell_ddd.domain.repositories.template_graph_repository import TemplateGraphRepository
from shell_ddd.domain.repositories.workflow_repository import WorkflowRepository

__all__ = [
    "EnvelopeArchive",
    "EnvelopeRepository",
    "NodeResultRepository",
    "PromptRepository",
    "RagDocumentRepository",
    "RunnerConfigRepository",
    "SessionRepository",
    "TaskRepository",
    "TemplateGraphRepository",
    "WorkflowRepository",
]