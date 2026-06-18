from __future__ import annotations

from shell.application.dto.dto import (
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
from shell.domain.value_objects.ids import WorkflowId
from shell.infrastructure.persistence.memory.memory.in_memory_unit_of_work import InMemoryUnitOfWork


class InMemoryQueryServices:
    def __init__(self, uow: InMemoryUnitOfWork) -> None:
        self._uow = uow

    async def get_task_execution_by_name(self, name: str) -> TaskExecutionDto | None:
        task_execution = next(
            (task_execution for task_execution in self._uow.task_executions._store.values() if task_execution.name.value == name),  # type: ignore[attr-defined]
            None,
        )
        if not task_execution:
            return None
        graph_execution = await self._uow.graph_executions.get_by_task_execution_id(
            task_execution.id
        )
        graph_node_executions = []
        if graph_execution is not None:
            from shell.application.dto.dto import GraphNodeExecutionDto

            graph_node_executions = [
                GraphNodeExecutionDto(
                    id=graph_node_execution.id.value,
                    position=graph_node_execution.position,
                    node_dir=graph_node_execution.node_dir,
                    mode=graph_node_execution.mode.value,
                    role=graph_node_execution.role,
                    node_type=graph_node_execution.node_type,
                    model=graph_node_execution.model,
                    command=graph_node_execution.command,
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
        workflow = self._uow.workflows._store.get(workflow_id)  # type: ignore[attr-defined]
        if not workflow:
            return None
        return WorkflowDto(
            id=str(workflow.id),
            task_execution_id=str(workflow.task_execution_id),
            status=workflow.status.value,
            created_at=workflow.created_at,
            graph_node_execution_states={
                str(state_id): GraphNodeExecutionStateDto(
                    graph_node_execution_id=str(state.graph_node_execution_id),
                    status=state.status.value,
                    step=state.step,
                    updated_at=state.updated_at,
                )
                for state_id, state in workflow.graph_node_execution_states.items()
            },
        )

    async def get_envelopes_by_workflow(
        self, workflow_id: str, pending_only: bool = False
    ) -> list[EnvelopeDto]:
        envelopes = [
            envelope
            for envelope in self._uow.envelopes._store.values()
            if str(envelope.workflow_id) == workflow_id  # type: ignore[attr-defined]
        ]
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
        wf = await self._uow.workflows.get_by_id(WorkflowId(workflow_id))
        if wf is None:
            return None
        res = wf.graph_node_execution_results.get(graph_node_execution_id)
        if not res:
            return None
        return GraphNodeExecutionResultDto(
            id=str(res.id),
            graph_node_execution_id=str(res.graph_node_execution_id),
            workflow_id=str(res.workflow_id),
            status=res.status.value,
            stdout=res.stdout,
            stderr=res.stderr,
            artifact_uri=res.artifact_uri,
            created_at=res.created_at,
        )

    async def get_prompt(self, name: str) -> PromptDto | None:
        prompt = next(
            (prompt for prompt in self._uow.prompts._store.values() if prompt.name == name and prompt.is_current),
            None,  # type: ignore[attr-defined]
        )
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
        c = await self._uow.runner_configs.get_by_package(package_name)
        if not c:
            return None
        return RunnerConfigDto(
            id=str(c.id),
            package_name=c.package_name,
            kind=c.kind,
            hash=str(c.hash),
            body=c.body,
            created_at=c.created_at,
        )

    async def get_session_history(self, session_id: str) -> SessionDto | None:
        session = self._uow.sessions._store.get(session_id)  # type: ignore[attr-defined]

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
        chunks = list(self._uow.rag_documents._store.values())  # type: ignore[attr-defined]
        return [
            RagChunkDto(
                chunk_id=f"chunk-{index}",
                document_id="doc-1",
                chunk_index=index,
                chunk_text="test content",
                source_uri="file://test.md",
                title="Test Doc",
                domain=domain or "default",
                score=1.0,
            )
            for index in range(min(top_k, len(chunks)))
        ]
