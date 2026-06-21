"""InMemory persistence adapters — backward-compat re-exports."""

from __future__ import annotations

import logging

from shell.infrastructure.definition.persistence.memory.in_memory_graph_definition_repository import (
    InMemoryGraphDefinitionRepository,
)
from shell.infrastructure.definition.persistence.memory.in_memory_graph_node_definition_repository import (
    InMemoryGraphNodeDefinitionRepository,
)
from shell.infrastructure.definition.persistence.memory.in_memory_prompt_repository import (
    InMemoryPromptRepository,
)
from shell.infrastructure.definition.persistence.memory.in_memory_rag_document_repository import (
    InMemoryRagDocumentRepository,
)
from shell.infrastructure.definition.persistence.memory.in_memory_runner_config_repository import (
    InMemoryRunnerConfigRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_envelope_archive import (
    InMemoryEnvelopeArchive,
)
from shell.infrastructure.execution.persistence.memory.in_memory_envelope_repository import (
    InMemoryEnvelopeRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_graph_execution_repository import (
    InMemoryGraphExecutionRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_session_repository import (
    InMemorySessionRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_task_execution_repository import (
    InMemoryTaskExecutionRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_workflow_repository import (
    InMemoryWorkflowRepository,
)
from shell.infrastructure.platform.persistence.memory.fake_clock import FakeClock
from shell.infrastructure.platform.persistence.memory.fake_event_publisher import FakeEventPublisher
from shell.infrastructure.platform.persistence.memory.fake_graph_node_execution_process_runner import (
    FakeGraphNodeExecutionProcessRunner,
)
from shell.infrastructure.platform.persistence.memory.fake_graph_node_execution_workspace import (
    FakeGraphNodeExecutionWorkspace,
)
from shell.infrastructure.platform.persistence.memory.fake_id_generator import FakeIdGenerator
from shell.infrastructure.platform.persistence.memory.fake_logger import FakeLogger
from shell.infrastructure.platform.persistence.memory.fake_task_loader import FakeTaskLoader
from shell.infrastructure.platform.persistence.memory.in_memory_query_services import (
    InMemoryQueryServices,
)
from shell.infrastructure.platform.persistence.memory.in_memory_unit_of_work import (
    InMemoryUnitOfWork,
)

logger = logging.getLogger(__name__)

__all__ = [
    "FakeClock", "FakeEventPublisher", "FakeIdGenerator", "FakeLogger", "FakeGraphNodeExecutionProcessRunner",
    "FakeGraphNodeExecutionWorkspace", "FakeTaskLoader", "InMemoryQueryServices", "InMemoryUnitOfWork",
    "InMemoryGraphDefinitionRepository", "InMemoryGraphNodeDefinitionRepository",
    "InMemoryPromptRepository", "InMemoryRagDocumentRepository", "InMemoryRunnerConfigRepository",
    "InMemoryEnvelopeArchive", "InMemoryEnvelopeRepository", "InMemoryGraphExecutionRepository",
    "InMemorySessionRepository", "InMemoryTaskExecutionRepository", "InMemoryWorkflowRepository",
]
