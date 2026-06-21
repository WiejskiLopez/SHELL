from __future__ import annotations

from shell.application.platform.dto import (
    EnvelopeDto,
    GraphNodeExecutionResultDto,
    GraphNodeExecutionStateDto,
    MessageDto,
    PromptDto,
    RagChunkDto,
    RunnerConfigDto,
    SessionDto,
    TaskExecutionDto,
    WorkflowDto,
)
from shell.domain.execution.value_objects.ids import (
    GraphNodeExecutionId,
    SessionId,
    WorkflowId,
)
from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName
from shell.infrastructure.platform.persistence.memory.in_memory_unit_of_work import (
    InMemoryUnitOfWork,  # noqa: TC002 — InMemoryUnitOfWork używany w konstruktorze InMemoryQueryServices
)


class InMemoryQueryServices:
    def __init__(self, uow: InMemoryUnitOfWork) -> None:
        self._uow = uow

    async def get_task_execution_by_name(self, name: str) -> TaskExecutionDto | None:

        task_execution = await self._uow.task_executions.get_by_name(TaskExecutionName(name))
        if not task_execution:
            return None
        graph_execution = await self._uow.graph_executions.get_by_task_execution_id(
            task_execution.id
        )
        graph_node_executions = []
        if graph_execution is not None:
            from shell.application.platform.dto import GraphNodeExecutionDto

            graph_node_executions = [
                GraphNodeExecutionDto(
                    id=graph_node_execution.id.value,
                    position=graph_node_execution.position,
                    mode=graph_node_execution.mode.value,
                    role=graph_node_execution.role,
                    node_type=graph_node_execution.node_type,
                    model=graph_node_execution.model,
                    command=graph_node_execution.command,
                    sub_graph_definition_id=graph_node_execution.sub_graph_definition_id,
                    sub_graph_definition_version=graph_node_execution.sub_graph_definition_version,
                )
                for graph_node_execution in graph_execution.graph_node_executions
            ]
        return TaskExecutionDto(
            id=task_execution.id.value,
            name=task_execution.name.value,
            version=task_execution.version.value,
            hash=task_execution.hash.value,
            is_current=task_execution.is_current,
            created_at=task_execution.created_at,
            body=task_execution.body.value,
            graph_node_executions=graph_node_executions,
        )

    async def get_current_task(self, name: str) -> TaskExecutionDto | None:
        return await self.get_task_execution_by_name(name)

    async def get_workflow(self, workflow_id: str) -> WorkflowDto | None:
        workflow = await self._uow.workflows.get_by_id(WorkflowId(workflow_id))
        if not workflow:
            return None
        return WorkflowDto(
            id=str(workflow.id),
            status=workflow.status.value,
            created_at=workflow.created_at,
            version=workflow.version,
            cursor=workflow.cursor.current_graph_node_execution_id.value
            if workflow.cursor.current_graph_node_execution_id
            else None,
            graph_node_execution_states={
                str(state.graph_node_execution_id): GraphNodeExecutionStateDto(
                    graph_node_execution_id=str(state.graph_node_execution_id),
                    status=state.status.value,
                    step=state.step,
                    updated_at=state.updated_at,
                )
                for state in workflow.graph_node_execution_states
            },
        )

    async def get_envelopes_by_workflow(
        self, workflow_id: str, pending_only: bool = False
    ) -> list[EnvelopeDto]:
        envelopes = await self._uow.envelopes.list_by_workflow(WorkflowId(workflow_id))
        if pending_only:
            envelopes = [envelope for envelope in envelopes if envelope.status.value == "pending"]

        return [
            EnvelopeDto(
                id=str(envelope.id),
                workflow_id=str(envelope.workflow_id),
                sender_graph_node_execution_id=str(envelope.sender_graph_node_execution_id),
                receiver_graph_node_execution_id=str(envelope.receiver_graph_node_execution_id),
                source_role=envelope.source_role,
                target_role=envelope.target_role,
                status=envelope.status.value,
                stage=envelope.stage.value,
                step=envelope.step,
                payload=envelope.payload,
                created_at=envelope.created_at,
                updated_at=envelope.updated_at,
            )
            for envelope in envelopes
        ]

    async def get_graph_node_execution_result(
        self, graph_node_execution_id: str, workflow_id: str
    ) -> GraphNodeExecutionResultDto | None:
        workflow = await self._uow.workflows.get_by_id(WorkflowId(workflow_id))
        if workflow is None:
            return None

        result = workflow.get_graph_node_execution_result(GraphNodeExecutionId(graph_node_execution_id))
        if result is None:
            return None
        return GraphNodeExecutionResultDto(
            id=str(result.id),
            graph_node_execution_id=str(result.graph_node_execution_id),
            workflow_id=str(result.workflow_id),
            status=result.status.value,
            stdout=result.stdout,
            stderr=result.stderr,
            artifact_uri=result.artifact_uri,
            created_at=result.created_at,
        )

    async def get_prompt(self, name: str) -> PromptDto | None:
        prompt = await self._uow.prompts.get_current_by_name(name)
        if not prompt:
            return None
        return PromptDto(
            id=str(prompt.id),
            name=prompt.name,
            version=prompt.version,
            hash=str(prompt.hash),
            body=prompt.body,
            is_current=prompt.is_current,
            created_at=prompt.created_at,
        )

    async def get_runner_config(self, package_name: str) -> RunnerConfigDto | None:
        runner_config = await self._uow.runner_configs.get_by_package(package_name)
        if not runner_config:
            return None
        return RunnerConfigDto(
            id=str(runner_config.id),
            package_name=runner_config.package_name,
            kind=runner_config.kind,
            hash=str(runner_config.hash),
            body=runner_config.body,
            created_at=runner_config.created_at,
        )

    async def get_session_history(self, session_id: str) -> SessionDto | None:
        session = await self._uow.sessions.get_by_id(SessionId(session_id))
        if session is None:
            return None

        return SessionDto(
            id=session.id.value,
            goal=session.goal,
            status=session.status,
            opened_at=session.opened_at,
            closed_at=session.closed_at,
            messages=[
                MessageDto(
                    id=message.id.value,
                    session_id=message.session_id.value,
                    correlation_id=message.correlation_id.value,
                    sender=message.sender,
                    receiver=message.receiver,
                    payload=message.payload,
                    created_at=message.created_at,
                )
                for message in session.messages
            ],
        )

    async def search_similar(
        self, query_embedding: bytes, top_k: int = 5, domain: str | None = None
    ) -> list[RagChunkDto]:
        chunks = await self._uow.rag_documents.search_similar(query_embedding, top_k, domain)
        return [
            RagChunkDto(
                chunk_id=chunk.id.value,
                document_id=chunk.document_id.value,
                chunk_index=chunk.chunk_index,
                chunk_text=chunk.chunk_text,
                source_uri="",
                title="",
                domain=domain or "",
                score=1.0,
            )
            for chunk in chunks
        ]
