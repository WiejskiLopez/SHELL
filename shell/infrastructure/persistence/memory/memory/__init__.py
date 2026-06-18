"""InMemory persistence adapters for unit tests."""

from __future__ import annotations

import logging

from shell.infrastructure.persistence.memory.memory.in_memory_task_execution_repository import InMemoryTaskExecutionRepository
from shell.infrastructure.persistence.memory.memory.in_memory_graph_execution_repository import InMemoryGraphExecutionRepository
from shell.infrastructure.persistence.memory.memory.in_memory_workflow_repository import InMemoryWorkflowRepository
from shell.infrastructure.persistence.memory.memory.in_memory_envelope_repository import InMemoryEnvelopeRepository
from shell.infrastructure.persistence.memory.memory.in_memory_envelope_archive import InMemoryEnvelopeArchive
from shell.infrastructure.persistence.memory.memory.in_memory_prompt_repository import InMemoryPromptRepository
from shell.infrastructure.persistence.memory.memory.in_memory_runner_config_repository import InMemoryRunnerConfigRepository
from shell.infrastructure.persistence.memory.memory.in_memory_rag_document_repository import InMemoryRagDocumentRepository
from shell.infrastructure.persistence.memory.memory.in_memory_session_repository import InMemorySessionRepository
from shell.infrastructure.persistence.memory.memory.in_memory_unit_of_work import InMemoryUnitOfWork
from shell.infrastructure.persistence.memory.memory.fake_clock import FakeClock
from shell.infrastructure.persistence.memory.memory.fake_id_generator import FakeIdGenerator
from shell.infrastructure.persistence.memory.memory.fake_event_publisher import FakeEventPublisher
from shell.infrastructure.persistence.memory.memory.fake_logger import FakeLogger
from shell.infrastructure.persistence.memory.memory.fake_task_loader import FakeTaskLoader
from shell.infrastructure.persistence.memory.memory.fake_node_process_runner import FakeNodeProcessRunner
from shell.infrastructure.persistence.memory.memory.fake_node_workspace import FakeNodeWorkspace
from shell.infrastructure.persistence.memory.memory.in_memory_query_services import InMemoryQueryServices
from shell.infrastructure.persistence.memory.memory.in_memory_graph_definition_repository import InMemoryGraphDefinitionRepository
from shell.infrastructure.persistence.memory.memory.in_memory_graph_node_definition_repository import InMemoryGraphNodeDefinitionRepository

logger = logging.getLogger(__name__)

__all__ = [
    "InMemoryTaskExecutionRepository",
    "InMemoryGraphExecutionRepository",
    "InMemoryWorkflowRepository",
    "InMemoryEnvelopeRepository",
    "InMemoryEnvelopeArchive",
    "InMemoryPromptRepository",
    "InMemoryRunnerConfigRepository",
    "InMemoryRagDocumentRepository",
    "InMemorySessionRepository",
    "InMemoryUnitOfWork",
    "FakeClock",
    "FakeIdGenerator",
    "FakeEventPublisher",
    "FakeLogger",
    "FakeTaskLoader",
    "FakeNodeProcessRunner",
    "FakeNodeWorkspace",
    "InMemoryQueryServices",
    "InMemoryGraphDefinitionRepository",
    "InMemoryGraphNodeDefinitionRepository",
]
