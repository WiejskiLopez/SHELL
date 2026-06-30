from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.definition.dto.rag_chunk import RagChunkDto
from shell.application.definition.dto.runner_config import RunnerConfigDto
from shell.application.execution.dto.task_execution import TaskExecutionDto
from shell.application.execution.dto.workflow import WorkflowDto
from shell.application.session.dto.session import SessionDto
from shell.domain.definition.value_objects.package_name import PackageName
from shell.domain.execution.value_objects.ids import (
    WorkflowId,
)
from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName
from shell.domain.session.aggregates.session.value_objects.session_id import SessionId
from shell.infrastructure.definition.persistence.memory.in_memory_rag_document_repository import (
    InMemoryRagDocumentRepository,
)
from shell.infrastructure.definition.persistence.memory.in_memory_runner_config_repository import (
    InMemoryRunnerConfigRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_graph_execution_repository import (
    InMemoryGraphExecutionRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_graph_node_execution_repository import (
    InMemoryGraphNodeExecutionRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_task_execution_repository import (
    InMemoryTaskExecutionRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_workflow_repository import (
    InMemoryWorkflowRepository,
)
from shell.infrastructure.session.persistence.memory.in_memory_session_repository import (
    InMemorySessionRepository,
)

if TYPE_CHECKING:
    from shell.infrastructure.platform.persistence.memory.in_memory_unit_of_work import (
        InMemoryUnitOfWork,  # noqa: TC002 — InMemoryUnitOfWork używany w konstruktorze InMemoryQueryServices
    )


class InMemoryQueryServices:
    def __init__(self, unit_of_work: InMemoryUnitOfWork) -> None:
        self._unit_of_work = unit_of_work

    async def get_task_execution_by_name(self, name: str) -> TaskExecutionDto | None:

        task_execution = await self._unit_of_work.repository(
            InMemoryTaskExecutionRepository
        ).get_by_name(TaskExecutionName(name))
        if not task_execution:
            return None
        graph_execution = await self._unit_of_work.repository(
            InMemoryGraphExecutionRepository
        ).get_by_task_execution_id(task_execution.id)
        graph_node_executions = []
        if graph_execution is not None:
            from shell.application.execution.dto.graph_node_execution import GraphNodeExecutionDto

            nodes = await self._unit_of_work.repository(
                InMemoryGraphNodeExecutionRepository
            ).list_by_graph_execution_id(graph_execution.id)
            graph_node_executions = [
                GraphNodeExecutionDto(
                    id=graph_node_execution.id.value,
                    position=graph_node_execution.position.value,
                    mode=graph_node_execution.mode.value,
                    role=graph_node_execution.role,
                    node_type=graph_node_execution.node_type.value,
                    model=None,
                    command=None,
                )
                for graph_node_execution in nodes
            ]
        return TaskExecutionDto(
            id=task_execution.id.value,
            name=task_execution.name.value,
            created_at=task_execution.created_at.value if task_execution.created_at else None,
            graph_node_executions=tuple(graph_node_executions),
        )

    async def get_current_task(self, name: str) -> TaskExecutionDto | None:
        return await self.get_task_execution_by_name(name)

    async def get_workflow(self, workflow_id: str) -> WorkflowDto | None:
        workflow = await self._unit_of_work.repository(InMemoryWorkflowRepository).get_by_id(
            WorkflowId(workflow_id)
        )
        if not workflow:
            return None
        return WorkflowDto(
            id=str(workflow.id),
            status=workflow.status.value,
            created_at=workflow.created_at.value,
        )

    async def get_runner_config(self, package_name: str) -> RunnerConfigDto | None:
        runner_config = await self._unit_of_work.repository(
            InMemoryRunnerConfigRepository
        ).get_by_package(PackageName(package_name))
        if not runner_config:
            return None
        return RunnerConfigDto(
            id=str(runner_config.id),
            package_name=runner_config.package_name.value,
            kind=runner_config.kind.value,
            hash=str(runner_config.hash),
            body=dict(runner_config.body.value),
            created_at=runner_config.created_at.value,
        )

    async def get_session_history(self, session_id: str) -> SessionDto | None:
        session = await self._unit_of_work.repository(InMemorySessionRepository).get_by_id(
            SessionId(session_id)
        )
        if session is None:
            return None

        return SessionDto(
            id=session.id.value,
            goal=session.goal,
            status=session.status,
            opened_at=session.opened_at.value,
            closed_at=session.closed_at.value if session.closed_at else None,
        )

    async def search_similar(
        self, query_embedding: bytes, top_k: int = 5, domain: str | None = None
    ) -> list[RagChunkDto]:
        from shell.domain.definition.value_objects.chunk_index import ChunkIndex
        from shell.domain.definition.value_objects.domain_tag import DomainTag
        from shell.domain.definition.value_objects.embedding import Embedding

        chunks = await self._unit_of_work.repository(InMemoryRagDocumentRepository).search_similar(
            Embedding(query_embedding), ChunkIndex(top_k), DomainTag(domain) if domain else None
        )
        return [
            RagChunkDto(
                chunk_id=chunk.id.value,
                document_id=chunk.document_id.value,
                chunk_index=chunk.chunk_index.value,
                chunk_text=chunk.chunk_text.value,
                source_uri="",
                title="",
                domain=domain or "",
                score=1.0,
            )
            for chunk in chunks
        ]
