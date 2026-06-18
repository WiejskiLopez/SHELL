"""Repository port interfaces — re-exports from granular modules (backward compatibility)."""

from __future__ import annotations

from shell.domain.repositories.envelope_repository import EnvelopeArchive, EnvelopeRepository
from shell.domain.repositories.graph_definition_repository import GraphDefinitionRepository
from shell.domain.repositories.prompt_repository import PromptRepository
from shell.domain.repositories.rag_repository import RagDocumentRepository
from shell.domain.repositories.runner_config_repository import RunnerConfigRepository
from shell.domain.repositories.session_repository import SessionRepository
from shell.domain.repositories.task_execution_input_payload_repository import (
    TaskExecutionInputPayloadRepository,
)
from shell.domain.repositories.task_execution_output_payload_repository import (
    TaskExecutionOutputPayloadRepository,
)
from shell.domain.repositories.task_execution_repository import TaskExecutionRepository
from shell.domain.repositories.workflow_repository import WorkflowRepository

__all__ = [
    "EnvelopeArchive",
    "EnvelopeRepository",
    "GraphDefinitionRepository",
    "PromptRepository",
    "RagDocumentRepository",
    "RunnerConfigRepository",
    "SessionRepository",
    "TaskExecutionInputPayloadRepository",
    "TaskExecutionOutputPayloadRepository",
    "TaskExecutionRepository",
    "WorkflowRepository",
]
