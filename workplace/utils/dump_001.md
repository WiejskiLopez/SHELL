### __init__.py
```
```

### application/__init__.py
```
```

### application/bus.py
```
"""In-memory CommandBus, QueryBus, EventBus."""
from __future__ import annotations

from typing import Any


class CommandBus:
    """Routes commands to their registered handlers."""

    def __init__(self) -> None:
        self._handlers: dict[type[Any], Any] = {}

    def register(self, command_type: type[Any], handler: Any) -> None:
        self._handlers[command_type] = handler

    async def dispatch(self, command: Any) -> Any:
        handler = self._handlers.get(type(command))
        if handler is None:
            raise KeyError(f"No handler registered for {type(command).__name__}")
        return await handler.handle(command)


class QueryBus:
    """Routes queries to their registered handlers."""

    def __init__(self) -> None:
        self._handlers: dict[type[Any], Any] = {}

    def register(self, query_type: type[Any], handler: Any) -> None:
        self._handlers[query_type] = handler

    async def dispatch(self, query: Any) -> Any:
        handler = self._handlers.get(type(query))
        if handler is None:
            raise KeyError(f"No handler registered for {type(query).__name__}")
        return await handler.handle(query)


class EventBus:
    """In-memory event bus — publishes domain events to registered subscribers."""

    def __init__(self) -> None:
        self._subscribers: dict[type[Any], list[Any]] = {}

    def subscribe(self, event_type: type[Any], handler: Any) -> None:
        self._subscribers.setdefault(event_type, []).append(handler)

    async def publish(self, events: list[Any]) -> None:
        for event in events:
            for handler in self._subscribers.get(type(event), []):
                await handler.handle(event)
```

### application/command_handlers/__init__.py
```
```

### application/command_handlers/archive_envelope_handler.py
```
"""ArchiveEnvelopeHandler — marks an envelope as archived."""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell_ddd.domain.exceptions import EnvelopeNotFound
from shell_ddd.domain.value_objects.envelope_status import EnvelopeStage
from shell_ddd.domain.value_objects.ids import EnvelopeId

if TYPE_CHECKING:
    from shell_ddd.application.commands.commands import ArchiveEnvelopeCommand
    from shell_ddd.application.ports.ports import Clock, EventPublisher, UnitOfWork


class ArchiveEnvelopeHandler:
    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        events: EventPublisher,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._events = events

    async def handle(self, cmd: ArchiveEnvelopeCommand) -> None:
        env_id = EnvelopeId(cmd.envelope_id)
        now = self._clock.now()

        async with self._uow as uow:
            envelope = await uow.envelopes.get_by_id(env_id)
            if envelope is None:
                raise EnvelopeNotFound(cmd.envelope_id)

            archive_uri = await uow.envelope_archive.archive(envelope)
            envelope.archive_uri = archive_uri
            envelope.transition_stage(EnvelopeStage.ARCHIVED, now)
            await uow.envelopes.save(envelope)
            await uow.commit()
```

### application/command_handlers/bootstrap_runner_config_handler.py
```
"""BootstrapRunnerConfigHandler."""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell_ddd.domain.entities.runner_config import RunnerConfig

if TYPE_CHECKING:
    from shell_ddd.application.commands.commands import BootstrapRunnerConfigCommand
    from shell_ddd.application.ports.ports import Clock, IdGenerator, UnitOfWork


class BootstrapRunnerConfigHandler:
    def __init__(self, uow: UnitOfWork, clock: Clock, id_gen: IdGenerator) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen

    async def handle(self, cmd: BootstrapRunnerConfigCommand) -> str:
        async with self._uow as uow:
            config = RunnerConfig.new(
                id_=self._id_gen.new_runner_config_id(),
                package_name=cmd.package_name,
                kind=cmd.kind,
                body=cmd.body,
                now=self._clock.now(),
            )
            await uow.runner_configs.save(config)
            await uow.commit()
        return config.id.value
```

### application/command_handlers/import_task_handler.py
```
"""ImportTaskHandler — imports a task from markdown + yaml files."""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell_ddd.domain.entities.task import Task
from shell_ddd.domain.events.events import TaskImported
from shell_ddd.domain.value_objects.task_name import TaskName

if TYPE_CHECKING:
    from shell_ddd.application.commands.commands import ImportTaskCommand
    from shell_ddd.application.ports.ports import (
        Clock,
        EventPublisher,
        IdGenerator,
        TaskLoader,
        UnitOfWork,
    )


class ImportTaskHandler:
    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        task_loader: TaskLoader,
        events: EventPublisher,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._task_loader = task_loader
        self._events = events

    async def handle(self, cmd: ImportTaskCommand) -> str:
        body_md, body_yaml_raw = await self._task_loader.load(cmd.md_path, cmd.yaml_path)
        name = TaskName(cmd.task_name)
        task = Task.new(
            id_=self._id_gen.new_task_id(),
            name=name,
            body_md=body_md,
            body_yaml_raw=body_yaml_raw,
            now=self._clock.now(),
        )
        async with self._uow as uow:
            # mark previous versions non-current
            existing = await uow.tasks.get_current_by_name(name)
            if existing:
                existing.is_current = False
                await uow.tasks.save(existing)
            await uow.tasks.save(task)
            await uow.commit()
        await self._events.publish([TaskImported.now(task.id, name)])
        return task.id.value
```

### application/command_handlers/index_document_handler.py
```
"""IndexDocumentHandler — chunk, embed, persist a RAG document."""
from __future__ import annotations

from shell_ddd.application.commands.commands import IndexDocumentCommand
from shell_ddd.application.ports.ports import Clock, IdGenerator, UnitOfWork
from shell_ddd.domain.services.rag_index_service import Embedder, build_rag_document
from shell_ddd.domain.value_objects.ids import RagDocumentId


class IndexDocumentHandler:
    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        embedder: Embedder,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._embedder = embedder

    async def handle(self, cmd: IndexDocumentCommand) -> RagDocumentId:
        doc_id = self._id_gen.new_rag_document_id()
        # pre-generate enough chunk IDs (max chunks = ceil(len/step))
        max_chunks = max(1, len(cmd.text) // max(1, cmd.chunk_size - cmd.overlap) + 2)
        chunk_ids = [self._id_gen.new_rag_chunk_id() for _ in range(max_chunks)]
        doc = build_rag_document(
            doc_id=doc_id,
            chunk_ids=chunk_ids,
            source_uri=cmd.source_uri,
            title=cmd.title,
            domain=cmd.domain,
            text=cmd.text,
            embedder=self._embedder,
            now=self._clock.now(),
            chunk_size=cmd.chunk_size,
            overlap=cmd.overlap,
        )
        async with self._uow as uow:
            await uow.rag_documents.save(doc)
            await uow.commit()
        return doc_id
```

### application/command_handlers/route_envelopes_handler.py
```
"""RouteEnvelopesHandler — routes PENDING envelopes for a workflow."""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell_ddd.domain.events.events import EnvelopeExpired, EnvelopeRouted
from shell_ddd.domain.exceptions import WorkflowNotFound
from shell_ddd.domain.services.envelope_lifecycle_service import EnvelopeLifecycleService
from shell_ddd.domain.services.graph_routing_service import GraphRoutingService
from shell_ddd.domain.value_objects.envelope_status import EnvelopeStage, EnvelopeStatus
from shell_ddd.domain.value_objects.ids import WorkflowId
from shell_ddd.domain.value_objects.task_name import TaskName

if TYPE_CHECKING:
    from shell_ddd.application.commands.commands import RouteEnvelopesCommand
    from shell_ddd.application.ports.ports import Clock, EventPublisher, UnitOfWork
    from shell_ddd.domain.events.events import DomainEvent


class RouteEnvelopesHandler:
    """Routes PENDING envelopes to the correct receiver_node_id using the task graph.

    - Envelopes exceeding max_step are expired (DEAD).
    - Remaining PENDING envelopes are resolved to a receiver and moved to ACTIVE.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        events: EventPublisher,
        max_step: int = 0,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._events = events
        self._max_step = max_step

    async def handle(self, cmd: RouteEnvelopesCommand) -> int:
        """Process envelopes and return the number of envelopes routed."""
        wf_id = WorkflowId(cmd.workflow_id)
        published: list[DomainEvent] = []

        async with self._uow as uow:
            workflow = await uow.workflows.get_by_id(wf_id)
            if workflow is None:
                raise WorkflowNotFound(cmd.workflow_id)

            pending = await uow.envelopes.list_pending(wf_id)
            task = await uow.tasks.get_current_by_name(TaskName(workflow.task_name))

            now = self._clock.now()
            routed = 0

            for envelope in pending:
                new_status = EnvelopeLifecycleService.advance(envelope, self._max_step)
                if new_status == EnvelopeStatus.DEAD:
                    envelope.transition_status(EnvelopeStatus.DEAD, now)
                    await uow.envelopes.save(envelope)
                    published.append(EnvelopeExpired.now(envelope.id, envelope.workflow_id))
                    continue

                if task is not None and task.graph is not None:
                    try:
                        target_node_id = GraphRoutingService.resolve_target_node(
                            task.graph,
                            envelope.sender_node_id,
                            envelope.target_role or None,
                        )
                        envelope.receiver_node_id = target_node_id
                    except Exception:
                        continue  # Unresolvable — leave PENDING

                envelope.transition_status(EnvelopeStatus.ACTIVE, now)
                envelope.transition_stage(EnvelopeStage.SENT, now)
                await uow.envelopes.save(envelope)
                published.append(EnvelopeRouted.now(envelope.id, envelope.workflow_id))
                routed += 1

            await uow.commit()

        await self._events.publish(published)
        return routed
```

### application/command_handlers/run_node_handler.py
```
"""RunNodeHandler — executes a node within a workflow using the appropriate strategy."""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell_ddd.domain.entities.node_result import NodeResult
from shell_ddd.domain.events.events import NodeCompleted, NodeFailed
from shell_ddd.domain.exceptions import WorkflowNotFound
from shell_ddd.domain.value_objects.ids import NodeId, WorkflowId
from shell_ddd.domain.value_objects.status import Status

if TYPE_CHECKING:
    from shell_ddd.application.commands.commands import RunNodeCommand
    from shell_ddd.application.ports.ports import (
        Clock,
        EventPublisher,
        IdGenerator,
        NodeProcessRunner,
        NodeWorkspace,
        UnitOfWork,
    )
    from shell_ddd.application.strategies.node_execution_strategy import NodeExecutionStrategy
    from shell_ddd.domain.events.events import DomainEvent


class RunNodeHandler:
    """Executes a graph node via the registered NodeExecutionStrategy for its mode.

    Saves a NodeResult, updates Workflow.node_states, and publishes NodeCompleted/NodeFailed.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        workspace: NodeWorkspace,
        runner: NodeProcessRunner,
        strategy: NodeExecutionStrategy,
        events: EventPublisher,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._workspace = workspace
        self._runner = runner
        self._strategy = strategy
        self._events = events

    async def handle(self, cmd: RunNodeCommand) -> str:
        """Execute node and return NodeResult id."""
        wf_id = WorkflowId(cmd.workflow_id)
        node_id = NodeId(cmd.node_id)
        published: list[DomainEvent] = []
        now = self._clock.now()

        async with self._uow as uow:
            workflow = await uow.workflows.get_by_id(wf_id)
            if workflow is None:
                raise WorkflowNotFound(cmd.workflow_id)

            workflow.update_node_state(node_id, Status.running())
            await uow.workflows.save(workflow)
            await uow.commit()

        # Execute strategy (outside UoW — may take a long time)
        try:
            result = await self._strategy.execute(
                node_id=cmd.node_id,
                workspace_path=cmd.workspace_path,
                runner=self._runner,
            )
            node_status = Status.done()
        except Exception as exc:
            # Capture failure without re-raising so we can persist result
            result_status = Status.failed()
            node_result_id = self._id_gen.new_node_result_id()
            node_result = NodeResult.new(
                id_=node_result_id,
                node_id=node_id,
                workflow_id=wf_id,
                status=result_status,
                stderr=str(exc),
                now=now,
            )
            async with self._uow as uow:
                await uow.node_results.save(node_result)
                wf = await uow.workflows.get_by_id(wf_id)
                if wf:
                    wf.update_node_state(node_id, result_status)
                    await uow.workflows.save(wf)
                await uow.commit()
            published.append(NodeFailed.now(node_id, wf_id, str(exc)))
            await self._events.publish(published)
            return node_result_id.value

        node_result_id = self._id_gen.new_node_result_id()
        node_result = NodeResult.new(
            id_=node_result_id,
            node_id=node_id,
            workflow_id=wf_id,
            status=node_status,
            stdout=result.stdout,
            stderr=result.stderr,
            artifact_uri="",
            now=now,
        )

        async with self._uow as uow:
            await uow.node_results.save(node_result)
            wf = await uow.workflows.get_by_id(wf_id)
            if wf:
                wf.update_node_state(node_id, node_status)
                await uow.workflows.save(wf)
            await uow.commit()

        published.append(NodeCompleted.now(node_id, wf_id, node_result_id))
        await self._events.publish(published)
        return node_result_id.value
```

### application/command_handlers/run_tasker_workflow_handler.py
```
"""RunTaskerWorkflowHandler — orchestrates concurrent execution of all graph nodes."""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from shell_ddd.domain.entities.node_result import NodeResult
from shell_ddd.domain.entities.workflow import Workflow
from shell_ddd.domain.events.events import (
    DomainEvent,
    NodeCompleted,
    NodeFailed,
    WorkflowCompleted,
    WorkflowFailed,
    WorkflowStarted,
)
from shell_ddd.domain.exceptions import TaskNotFound
from shell_ddd.domain.value_objects.ids import NodeId, NodeResultId
from shell_ddd.domain.value_objects.manifest import Manifest
from shell_ddd.domain.value_objects.mode import Mode
from shell_ddd.domain.value_objects.status import Status
from shell_ddd.domain.value_objects.task_name import TaskName

if TYPE_CHECKING:
    from shell_ddd.application.commands.commands import RunTaskerWorkflowCommand
    from shell_ddd.application.ports.ports import (
        Clock,
        EventPublisher,
        IdGenerator,
        NodeProcessRunner,
        UnitOfWork,
    )
    from shell_ddd.domain.entities.task import GraphNode
    from shell_ddd.domain.value_objects.execution_result import ExecutionResult


class RunTaskerWorkflowHandler:
    """Executes all nodes of a task graph concurrently and persists their results.

    Workflow lifecycle:
    1. Load task + graph from UoW.
    2. Create a new Workflow, mark it ``running``.
    3. Run all non-router nodes concurrently (Semaphore controls parallelism).
    4. Persist NodeResult per node, update Workflow.node_states.
    5. Mark workflow COMPLETED (all done) or FAILED (any failed).
    6. Publish NodeCompleted/NodeFailed + WorkflowCompleted/WorkflowFailed.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        runner: NodeProcessRunner,
        events: EventPublisher,
        max_parallel: int = 4,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._runner = runner
        self._events = events
        self._max_parallel = max_parallel

    async def handle(self, cmd: RunTaskerWorkflowCommand) -> str:
        """Run all task graph nodes concurrently; return the workflow id."""
        task_name = TaskName(cmd.task_name)
        effective_parallel = cmd.max_parallel or self._max_parallel

        # ── 1. Load task ──────────────────────────────────────────────────
        async with self._uow as uow:
            task = await uow.tasks.get_current_by_name(task_name)
            if task is None:
                raise TaskNotFound(cmd.task_name)
            nodes: list[GraphNode] = list(task.graph.nodes) if task.graph else []

            # ── 2. Create Workflow ─────────────────────────────────────────
            workflow = Workflow.new(
                id_=self._id_gen.new_workflow_id(),
                task_name=cmd.task_name,
                now=self._clock.now(),
            )
            workflow.start()
            await uow.workflows.save(workflow)
            await uow.commit()

        workflow_id = workflow.id
        await self._events.publish([WorkflowStarted.now(workflow_id, cmd.task_name)])

        # ── 3. Execute all nodes concurrently ─────────────────────────────
        semaphore = asyncio.Semaphore(effective_parallel)

        async def _run_one(node: GraphNode) -> tuple[str, bool, str, str]:
            """Run a single node; return (node_id_str, success, stdout, stderr)."""
            async with semaphore:
                manifest = Manifest(
                    name=node.id.value,
                    mode=Mode(node.mode.value) if not isinstance(node.mode, Mode) else node.mode,
                    role=node.role or node.mode.value,
                    node_type=node.node_type or node.mode.value,
                    version="1",
                )
                env: dict[str, str] = {
                    "SHELL_DDD_WORKFLOW_ID": workflow_id.value,
                    "SHELL_DDD_NODE_ID": node.id.value,
                    "SHELL_DDD_TASK_NAME": cmd.task_name,
                }
                try:
                    result: ExecutionResult = await self._runner.run(
                        manifest, cmd.work_dir, env
                    )
                    return (node.id.value, result.success, result.stdout, result.stderr)
                except Exception as exc:  # noqa: BLE001
                    return (node.id.value, False, "", str(exc))

        exec_results: list[tuple[str, bool, str, str]] = list(
            await asyncio.gather(*[_run_one(n) for n in nodes])
        )

        # ── 4. Persist NodeResults + update Workflow ──────────────────────
        all_ok = all(ok for _, ok, _, _ in exec_results)
        now = self._clock.now()
        node_result_ids: dict[str, NodeResultId] = {}

        async with self._uow as uow:
            wf = await uow.workflows.get_by_id(workflow_id)
            for node_id_str, ok, stdout, stderr in exec_results:
                node_id = NodeId(node_id_str)
                node_status = Status.done() if ok else Status.failed()
                nr_id = self._id_gen.new_node_result_id()
                node_result_ids[node_id_str] = nr_id
                nr = NodeResult.new(
                    id_=nr_id,
                    node_id=node_id,
                    workflow_id=workflow_id,
                    status=node_status,
                    stdout=stdout,
                    stderr=stderr,
                    now=now,
                )
                await uow.node_results.save(nr)
                if wf:
                    wf.update_node_state(node_id, node_status)
            if wf:
                if all_ok:
                    wf.complete()
                else:
                    wf.fail()
                await uow.workflows.save(wf)
            await uow.commit()

        # ── 5. Publish events ─────────────────────────────────────────────
        domain_events: list[DomainEvent] = []
        for node_id_str, ok, _, reason in exec_results:
            node_id = NodeId(node_id_str)
            if ok:
                domain_events.append(
                    NodeCompleted.now(node_id, workflow_id, node_result_ids[node_id_str])
                )
            else:
                domain_events.append(NodeFailed.now(node_id, workflow_id, reason))
        if all_ok:
            domain_events.append(WorkflowCompleted.now(workflow_id, cmd.task_name))
        else:
            domain_events.append(WorkflowFailed.now(workflow_id, cmd.task_name))
        await self._events.publish(domain_events)

        return workflow_id.value
```

### application/command_handlers/save_node_result_handler.py
```
"""SaveNodeResultHandler."""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell_ddd.domain.entities.node_result import NodeResult
from shell_ddd.domain.events.events import NodeCompleted, NodeFailed
from shell_ddd.domain.value_objects.ids import NodeId, WorkflowId
from shell_ddd.domain.value_objects.status import Status

if TYPE_CHECKING:
    from shell_ddd.application.commands.commands import SaveNodeResultCommand
    from shell_ddd.application.ports.ports import Clock, EventPublisher, IdGenerator, UnitOfWork


class SaveNodeResultHandler:
    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        events: EventPublisher,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._events = events

    async def handle(self, cmd: SaveNodeResultCommand) -> str:
        node_id = NodeId(cmd.node_id)
        workflow_id = WorkflowId(cmd.workflow_id)
        status = Status(cmd.status)
        result = NodeResult.new(
            id_=self._id_gen.new_node_result_id(),
            node_id=node_id,
            workflow_id=workflow_id,
            status=status,
            stdout=cmd.stdout,
            stderr=cmd.stderr,
            artifact_uri=cmd.artifact_uri,
            now=self._clock.now(),
        )
        async with self._uow as uow:
            await uow.node_results.save(result)
            await uow.commit()
        if status == Status.done():
            await self._events.publish([NodeCompleted.now(node_id, workflow_id, result.id)])
        elif status == Status.failed():
            await self._events.publish([NodeFailed.now(node_id, workflow_id, cmd.stderr)])
        return result.id.value
```

### application/command_handlers/save_prompt_handler.py
```
"""SavePromptHandler."""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell_ddd.domain.entities.prompt import Prompt

if TYPE_CHECKING:
    from shell_ddd.application.commands.commands import SavePromptCommand
    from shell_ddd.application.ports.ports import Clock, IdGenerator, UnitOfWork


class SavePromptHandler:
    def __init__(self, uow: UnitOfWork, clock: Clock, id_gen: IdGenerator) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen

    async def handle(self, cmd: SavePromptCommand) -> str:
        async with self._uow as uow:
            existing = await uow.prompts.get_current_by_name(cmd.name)
            if existing:
                existing.is_current = False
                await uow.prompts.save(existing)
            prompt = Prompt.new(
                id_=self._id_gen.new_prompt_id(),
                name=cmd.name,
                body=cmd.body,
                source_uri=cmd.source_uri,
                now=self._clock.now(),
            )
            await uow.prompts.save(prompt)
            await uow.commit()
        return prompt.id.value
```

### application/command_handlers/session_handlers.py
```
"""OpenSessionHandler, CloseSessionHandler, AppendMessageHandler."""
from __future__ import annotations

from shell_ddd.application.commands.commands import (
    AppendMessageCommand,
    CloseSessionCommand,
    OpenSessionCommand,
)
from shell_ddd.application.ports.ports import Clock, IdGenerator, UnitOfWork
from shell_ddd.domain.entities.session import Session
from shell_ddd.domain.exceptions import DomainError
from shell_ddd.domain.value_objects.ids import MessageId, SessionId


class SessionNotFound(DomainError):
    pass


class OpenSessionHandler:
    def __init__(self, uow: UnitOfWork, clock: Clock, id_gen: IdGenerator) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen

    async def handle(self, cmd: OpenSessionCommand) -> SessionId:
        session_id = self._id_gen.new_session_id()
        session = Session.open(
            id_=session_id,
            agent_id=cmd.agent_id,
            goal=cmd.goal,
            now=self._clock.now(),
        )
        async with self._uow as uow:
            await uow.sessions.save(session)
            await uow.commit()
        return session_id


class CloseSessionHandler:
    def __init__(self, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    async def handle(self, cmd: CloseSessionCommand) -> None:
        async with self._uow as uow:
            session = await uow.sessions.get_by_id(SessionId(cmd.session_id))
            if session is None:
                raise SessionNotFound(f"Session not found: {cmd.session_id}")
            session.close(self._clock.now())
            await uow.sessions.save(session)
            await uow.commit()


class AppendMessageHandler:
    def __init__(self, uow: UnitOfWork, clock: Clock, id_gen: IdGenerator) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen

    async def handle(self, cmd: AppendMessageCommand) -> MessageId:
        async with self._uow as uow:
            session = await uow.sessions.get_by_id(SessionId(cmd.session_id))
            if session is None:
                raise SessionNotFound(f"Session not found: {cmd.session_id}")
            msg_id = self._id_gen.new_message_id()
            session.append_message(
                msg_id=msg_id,
                sender=cmd.sender,
                receiver=cmd.receiver,
                payload=dict(cmd.payload),
                now=self._clock.now(),
            )
            await uow.sessions.save(session)
            await uow.commit()
        return msg_id
```

### application/command_handlers/start_workflow_handler.py
```
"""StartWorkflowHandler — creates a new Workflow for a task."""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell_ddd.domain.entities.workflow import Workflow
from shell_ddd.domain.events.events import WorkflowStarted
from shell_ddd.domain.exceptions import TaskNotFound
from shell_ddd.domain.value_objects.task_name import TaskName

if TYPE_CHECKING:
    from shell_ddd.application.commands.commands import StartWorkflowCommand
    from shell_ddd.application.ports.ports import Clock, EventPublisher, IdGenerator, UnitOfWork


class StartWorkflowHandler:
    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        id_gen: IdGenerator,
        events: EventPublisher,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_gen = id_gen
        self._events = events

    async def handle(self, cmd: StartWorkflowCommand) -> str:
        async with self._uow as uow:
            task = await uow.tasks.get_current_by_name(TaskName(cmd.task_name))
            if task is None:
                raise TaskNotFound(cmd.task_name)
            workflow = Workflow.new(
                id_=self._id_gen.new_workflow_id(),
                task_name=cmd.task_name,
                now=self._clock.now(),
            )
            workflow.start()
            await uow.workflows.save(workflow)
            await uow.commit()
        await self._events.publish([WorkflowStarted.now(workflow.id, cmd.task_name)])
        return workflow.id.value
```

### application/commands/__init__.py
```
```

### application/commands/commands.py
```
"""Application commands."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ImportTaskCommand:
    """Import a task from markdown + yaml files."""

    md_path: str
    yaml_path: str
    task_name: str


@dataclass(frozen=True, slots=True)
class StartWorkflowCommand:
    """Start a new workflow for a given task."""

    task_name: str


@dataclass(frozen=True, slots=True)
class RunNodeCommand:
    """Execute a node within a workflow."""

    workflow_id: str
    node_id: str
    workspace_path: str


@dataclass(frozen=True, slots=True)
class RouteEnvelopesCommand:
    """Process pending envelopes for a workflow."""

    workflow_id: str


@dataclass(frozen=True, slots=True)
class ArchiveEnvelopeCommand:
    """Archive a delivered envelope."""

    envelope_id: str


@dataclass(frozen=True, slots=True)
class SaveNodeResultCommand:
    """Persist the result of a node execution."""

    workflow_id: str
    node_id: str
    status: str
    stdout: str = ""
    stderr: str = ""
    artifact_uri: str = ""


@dataclass(frozen=True, slots=True)
class SavePromptCommand:
    """Upsert a prompt by name."""

    name: str
    body: str
    source_uri: str = ""


@dataclass(frozen=True, slots=True)
class BootstrapRunnerConfigCommand:
    """Persist runner configuration for a package."""

    package_name: str
    kind: str
    body: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class IndexDocumentCommand:
    """Chunk, embed and index a text document for RAG retrieval."""

    source_uri: str
    title: str
    domain: str
    text: str
    chunk_size: int = 500
    overlap: int = 50


@dataclass(frozen=True, slots=True)
class OpenSessionCommand:
    """Open a new conversation session."""

    agent_id: str
    goal: str


@dataclass(frozen=True, slots=True)
class CloseSessionCommand:
    """Close an existing session."""

    session_id: str


@dataclass(frozen=True, slots=True)
class AppendMessageCommand:
    """Append a message to an open session."""

    session_id: str
    sender: str
    receiver: str
    payload: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RunTaskerWorkflowCommand:
    """Execute all graph nodes of a task concurrently (tasker orchestration)."""

    task_name: str
    work_dir: str
    max_parallel: int = 4
```

### application/dto/__init__.py
```
```

### application/dto/dto.py
```
"""Application DTOs — read-side data transfer objects."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class TaskDto:
    id: str
    name: str
    version: int
    hash: str
    is_current: bool
    created_at: datetime
    graph_nodes: list[GraphNodeDto] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class GraphNodeDto:
    id: str
    position: int
    node_dir: str
    mode: str
    role: str
    node_type: str
    model: str
    command: str


@dataclass(frozen=True, slots=True)
class WorkflowDto:
    id: str
    task_name: str
    status: str
    created_at: datetime
    node_states: dict[str, NodeStateDto] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class NodeStateDto:
    node_id: str
    status: str
    step: int
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class EnvelopeDto:
    id: str
    workflow_id: str
    sender_node_id: str
    receiver_node_id: str
    source_role: str
    target_role: str
    status: str
    stage: str
    step: int
    payload: dict[str, object]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class NodeResultDto:
    id: str
    node_id: str
    workflow_id: str
    status: str
    stdout: str
    stderr: str
    artifact_uri: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class PromptDto:
    id: str
    name: str
    version: int
    hash: str
    body: str
    is_current: bool
    created_at: datetime


@dataclass(frozen=True, slots=True)
class RunnerConfigDto:
    id: str
    package_name: str
    kind: str
    hash: str
    body: dict[str, object]
    created_at: datetime


@dataclass(frozen=True, slots=True)
class RagChunkDto:
    chunk_id: str
    document_id: str
    chunk_index: int
    chunk_text: str
    source_uri: str
    title: str
    domain: str
    score: float = 0.0


@dataclass(frozen=True, slots=True)
class MessageDto:
    id: str
    session_id: str
    sender: str
    receiver: str
    payload: dict[str, object]
    created_at: datetime


@dataclass(frozen=True, slots=True)
class SessionDto:
    id: str
    agent_id: str
    goal: str
    status: str
    opened_at: datetime
    closed_at: datetime | None
    messages: list[MessageDto] = field(default_factory=list)
```

### application/event_handlers/__init__.py
```
```

### application/event_handlers/event_handlers.py
```
"""Application-level event handlers."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell_ddd.application.commands.commands import ArchiveEnvelopeCommand
    from shell_ddd.application.ports.ports import Logger, UnitOfWork
    from shell_ddd.domain.events.events import DomainEvent, EnvelopeRouted, NodeCompleted, NodeFailed


class ArchiveOnDeliveredHandler:
    """Subscribes to EnvelopeRouted and archives the envelope when it reaches DELIVERED stage."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, event: EnvelopeRouted) -> None:
        from shell_ddd.domain.value_objects.envelope_status import EnvelopeStatus, EnvelopeStage
        from shell_ddd.domain.value_objects.ids import EnvelopeId

        async with self._uow as uow:
            envelope = await uow.envelopes.get_by_id(EnvelopeId(event.envelope_id.value))
            if envelope is None:
                return
            if envelope.status != EnvelopeStatus.DELIVERED:
                return
            archive_uri = await uow.envelope_archive.archive(envelope)
            envelope.archive_uri = archive_uri
            envelope.transition_stage(EnvelopeStage.ARCHIVED)
            await uow.envelopes.save(envelope)
            await uow.commit()


class LogAuditHandler:
    """Subscribes to all domain events and logs them for audit purposes."""

    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    async def handle(self, event: DomainEvent) -> None:
        self._logger.info(
            "domain_event",
            event_type=type(event).__name__,
            occurred_at=str(event.occurred_at),
        )
```

### application/mappers/__init__.py
```
```

### application/mappers/mappers.py
```
"""Domain entity → DTO mappers."""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell_ddd.application.dto.dto import (
    EnvelopeDto,
    GraphNodeDto,
    NodeResultDto,
    NodeStateDto,
    PromptDto,
    RunnerConfigDto,
    TaskDto,
    WorkflowDto,
)

if TYPE_CHECKING:
    from shell_ddd.domain.entities.envelope import Envelope
    from shell_ddd.domain.entities.node_result import NodeResult
    from shell_ddd.domain.entities.prompt import Prompt
    from shell_ddd.domain.entities.runner_config import RunnerConfig
    from shell_ddd.domain.entities.task import Task
    from shell_ddd.domain.entities.workflow import Workflow


def task_to_dto(task: Task) -> TaskDto:
    nodes: list[GraphNodeDto] = []
    if task.graph:
        nodes = [
            GraphNodeDto(
                id=n.id.value,
                position=n.position,
                node_dir=n.node_dir,
                mode=n.mode.value,
                role=n.role,
                node_type=n.node_type,
                model=n.model,
                command=n.command,
            )
            for n in task.graph.nodes
        ]
    return TaskDto(
        id=task.id.value,
        name=task.name.value,
        version=task.version,
        hash=task.hash.value,
        is_current=task.is_current,
        created_at=task.created_at,
        graph_nodes=nodes,
    )


def workflow_to_dto(workflow: Workflow) -> WorkflowDto:
    states = {
        k: NodeStateDto(
            node_id=v.node_id.value,
            status=v.status.value,
            step=v.step,
            updated_at=v.updated_at,
        )
        for k, v in workflow.node_states.items()
    }
    return WorkflowDto(
        id=workflow.id.value,
        task_name=workflow.task_name,
        status=workflow.status.value,
        created_at=workflow.created_at,
        node_states=states,
    )


def envelope_to_dto(envelope: Envelope) -> EnvelopeDto:
    return EnvelopeDto(
        id=envelope.id.value,
        workflow_id=envelope.workflow_id.value,
        sender_node_id=envelope.sender_node_id.value,
        receiver_node_id=envelope.receiver_node_id.value,
        source_role=envelope.source_role,
        target_role=envelope.target_role,
        status=envelope.status.value,
        stage=envelope.stage.value,
        step=envelope.step,
        payload=envelope.payload,
        created_at=envelope.created_at,
        updated_at=envelope.updated_at,
    )


def node_result_to_dto(result: NodeResult) -> NodeResultDto:
    return NodeResultDto(
        id=result.id.value,
        node_id=result.node_id.value,
        workflow_id=result.workflow_id.value,
        status=result.status.value,
        stdout=result.stdout,
        stderr=result.stderr,
        artifact_uri=result.artifact_uri,
        created_at=result.created_at,
    )


def prompt_to_dto(prompt: Prompt) -> PromptDto:
    return PromptDto(
        id=prompt.id.value,
        name=prompt.name,
        version=prompt.version,
        hash=prompt.hash.value,
        body=prompt.body,
        is_current=prompt.is_current,
        created_at=prompt.created_at,
    )


def runner_config_to_dto(config: RunnerConfig) -> RunnerConfigDto:
    return RunnerConfigDto(
        id=config.id.value,
        package_name=config.package_name,
        kind=config.kind,
        hash=config.hash.value,
        body=config.body,
        created_at=config.created_at,
    )
```

### application/ports/__init__.py
```
```

### application/ports/ports.py
```
"""Application-level ports (Protocols consumed by handlers)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from datetime import datetime

    from shell_ddd.domain.events.events import DomainEvent
    from shell_ddd.domain.repositories.repositories import (
        EnvelopeArchive,
        EnvelopeRepository,
        NodeResultRepository,
        PromptRepository,
        RagDocumentRepository,
        RunnerConfigRepository,
        SessionRepository,
        TaskRepository,
        WorkflowRepository,
    )
    from shell_ddd.domain.value_objects.execution_result import ExecutionResult
    from shell_ddd.domain.value_objects.ids import (
        EnvelopeId,
        MessageId,
        NodeResultId,
        PromptId,
        RagChunkId,
        RagDocumentId,
        RunnerConfigId,
        SessionId,
        TaskId,
        WorkflowId,
    )
    from shell_ddd.domain.value_objects.manifest import Manifest


class UnitOfWork(Protocol):
    """Transactional boundary; concrete adapters implement __aenter__/__aexit__."""

    tasks: TaskRepository
    workflows: WorkflowRepository
    envelopes: EnvelopeRepository
    prompts: PromptRepository
    node_results: NodeResultRepository
    runner_configs: RunnerConfigRepository
    envelope_archive: EnvelopeArchive
    rag_documents: RagDocumentRepository
    sessions: SessionRepository

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
    async def __aenter__(self) -> UnitOfWork: ...
    async def __aexit__(self, *args: object) -> None: ...


class Clock(Protocol):
    def now(self) -> datetime: ...


class IdGenerator(Protocol):
    def new_task_id(self) -> TaskId: ...
    def new_workflow_id(self) -> WorkflowId: ...
    def new_envelope_id(self) -> EnvelopeId: ...
    def new_prompt_id(self) -> PromptId: ...
    def new_node_result_id(self) -> NodeResultId: ...
    def new_runner_config_id(self) -> RunnerConfigId: ...
    def new_rag_document_id(self) -> RagDocumentId: ...
    def new_rag_chunk_id(self) -> RagChunkId: ...
    def new_session_id(self) -> SessionId: ...
    def new_message_id(self) -> MessageId: ...


class EventPublisher(Protocol):
    async def publish(self, events: list[DomainEvent]) -> None: ...


class Logger(Protocol):
    def debug(self, msg: str, **kw: object) -> None: ...
    def info(self, msg: str, **kw: object) -> None: ...
    def warning(self, msg: str, **kw: object) -> None: ...
    def error(self, msg: str, **kw: object) -> None: ...


class TaskLoader(Protocol):
    """Reads task markdown + yaml from the filesystem."""

    async def load(self, md_path: str, yaml_path: str) -> tuple[str, str]:
        """Return (body_md, body_yaml_raw)."""
        ...


class NodeWorkspace(Protocol):
    """Manages the filesystem workspace for a node execution."""

    async def prepare(self, node_id: str, work_dir: str) -> str:
        """Prepare workspace and return its path."""
        ...

    async def cleanup(self, workspace_path: str) -> None: ...


class NodeProcessRunner(Protocol):
    """Runs a node subprocess and returns its result."""

    async def run(
        self,
        manifest: Manifest,
        workspace_path: str,
        env: dict[str, str] | None = None,
    ) -> ExecutionResult: ...
```

### application/queries/__init__.py
```
```

### application/queries/queries.py
```
"""Application queries."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetTaskByNameQuery:
    name: str


@dataclass(frozen=True, slots=True)
class GetCurrentTaskQuery:
    name: str


@dataclass(frozen=True, slots=True)
class GetWorkflowQuery:
    workflow_id: str


@dataclass(frozen=True, slots=True)
class GetEnvelopesByWorkflowQuery:
    workflow_id: str
    pending_only: bool = False


@dataclass(frozen=True, slots=True)
class GetNodeResultQuery:
    node_id: str
    workflow_id: str


@dataclass(frozen=True, slots=True)
class GetPromptQuery:
    name: str


@dataclass(frozen=True, slots=True)
class GetRunnerConfigQuery:
    package_name: str


@dataclass(frozen=True, slots=True)
class SearchSimilarQuery:
    query_text: str
    top_k: int = 5
    domain: str | None = None


@dataclass(frozen=True, slots=True)
class GetSessionHistoryQuery:
    session_id: str
```

### application/query_handlers/__init__.py
```
```

### application/query_handlers/query_handlers.py
```
"""Query handlers — read-side, return DTOs."""
from __future__ import annotations

import struct
from typing import TYPE_CHECKING

from shell_ddd.application.mappers.mappers import (
    envelope_to_dto,
    node_result_to_dto,
    prompt_to_dto,
    runner_config_to_dto,
    task_to_dto,
    workflow_to_dto,
)
from shell_ddd.domain.services.rag_index_service import Embedder, _encode_vector, cosine_similarity
from shell_ddd.domain.value_objects.ids import NodeId, SessionId, WorkflowId
from shell_ddd.domain.value_objects.task_name import TaskName

if TYPE_CHECKING:
    from shell_ddd.application.dto.dto import (
        EnvelopeDto,
        MessageDto,
        NodeResultDto,
        PromptDto,
        RagChunkDto,
        RunnerConfigDto,
        SessionDto,
        TaskDto,
        WorkflowDto,
    )
    from shell_ddd.application.ports.ports import UnitOfWork
    from shell_ddd.application.queries.queries import (
        GetCurrentTaskQuery,
        GetEnvelopesByWorkflowQuery,
        GetNodeResultQuery,
        GetPromptQuery,
        GetRunnerConfigQuery,
        GetSessionHistoryQuery,
        GetTaskByNameQuery,
        GetWorkflowQuery,
        SearchSimilarQuery,
    )


class GetTaskByNameHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, query: GetTaskByNameQuery) -> TaskDto | None:
        async with self._uow as uow:
            task = await uow.tasks.get_by_name(TaskName(query.name))
            return task_to_dto(task) if task else None


class GetCurrentTaskHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, query: GetCurrentTaskQuery) -> TaskDto | None:
        async with self._uow as uow:
            task = await uow.tasks.get_current_by_name(TaskName(query.name))
            return task_to_dto(task) if task else None


class GetWorkflowHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, query: GetWorkflowQuery) -> WorkflowDto | None:
        async with self._uow as uow:
            wf = await uow.workflows.get_by_id(WorkflowId(query.workflow_id))
            return workflow_to_dto(wf) if wf else None


class GetEnvelopesByWorkflowHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, query: GetEnvelopesByWorkflowQuery) -> list[EnvelopeDto]:
        async with self._uow as uow:
            wf_id = WorkflowId(query.workflow_id)
            envelopes = (
                await uow.envelopes.list_pending(wf_id)
                if query.pending_only
                else await uow.envelopes.list_by_workflow(wf_id)
            )
            return [envelope_to_dto(e) for e in envelopes]


class GetNodeResultHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, query: GetNodeResultQuery) -> NodeResultDto | None:
        async with self._uow as uow:
            result = await uow.node_results.get_by_node_and_workflow(
                NodeId(query.node_id),
                WorkflowId(query.workflow_id),
            )
            return node_result_to_dto(result) if result else None


class GetPromptHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, query: GetPromptQuery) -> PromptDto | None:
        async with self._uow as uow:
            prompt = await uow.prompts.get_current_by_name(query.name)
            return prompt_to_dto(prompt) if prompt else None


class GetRunnerConfigHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, query: GetRunnerConfigQuery) -> RunnerConfigDto | None:
        async with self._uow as uow:
            config = await uow.runner_configs.get_by_package(query.package_name)
            return runner_config_to_dto(config) if config else None


class SearchSimilarHandler:
    def __init__(self, uow: UnitOfWork, embedder: Embedder) -> None:
        self._uow = uow
        self._embedder = embedder

    async def handle(self, query: SearchSimilarQuery) -> list[RagChunkDto]:
        from shell_ddd.application.dto.dto import RagChunkDto

        query_vec = self._embedder.embed_text(query.query_text)
        query_blob = _encode_vector(query_vec)
        async with self._uow as uow:
            chunks = await uow.rag_documents.search_similar(
                query_blob, top_k=query.top_k, domain=query.domain
            )
        results: list[RagChunkDto] = []
        for chunk in chunks:
            chunk_vec = list(
                struct.unpack(f"{len(chunk.embedding) // 4}f", chunk.embedding)
            )
            score = cosine_similarity(query_vec, chunk_vec)
            results.append(
                RagChunkDto(
                    chunk_id=chunk.id.value,
                    document_id=chunk.document_id.value,
                    chunk_index=chunk.chunk_index,
                    chunk_text=chunk.chunk_text,
                    source_uri="",
                    title="",
                    domain=query.domain or "",
                    score=score,
                )
            )
        results.sort(key=lambda r: r.score, reverse=True)
        return results[: query.top_k]


class GetSessionHistoryHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, query: GetSessionHistoryQuery) -> SessionDto | None:
        from shell_ddd.application.dto.dto import MessageDto, SessionDto

        async with self._uow as uow:
            session = await uow.sessions.get_by_id(SessionId(query.session_id))
            if session is None:
                return None
            messages = await uow.sessions.get_messages(session.id)
        return SessionDto(
            id=session.id.value,
            agent_id=session.agent_id,
            goal=session.goal,
            status=session.status,
            opened_at=session.opened_at,
            closed_at=session.closed_at,
            messages=[
                MessageDto(
                    id=m.id.value,
                    session_id=m.session_id.value,
                    sender=m.sender,
                    receiver=m.receiver,
                    payload=m.payload,
                    created_at=m.created_at,
                )
                for m in messages
            ],
        )
```

### application/strategies/__init__.py
```
```

### application/strategies/node_execution_strategy.py
```
"""NodeExecutionStrategy — port and 5 concrete implementations."""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell_ddd.application.ports.ports import NodeProcessRunner
    from shell_ddd.domain.value_objects.execution_result import ExecutionResult


class NodeExecutionStrategy(Protocol):
    """Strategy for executing a node; one implementation per mode."""

    async def execute(
        self,
        node_id: str,
        workspace_path: str,
        runner: NodeProcessRunner,
    ) -> ExecutionResult: ...


# ---------------------------------------------------------------------------
# Base helper
# ---------------------------------------------------------------------------

class _BaseStrategy:
    """Shared logic: build argv, call runner, return result."""

    mode: str  # overridden by subclasses

    async def execute(
        self,
        node_id: str,
        workspace_path: str,
        runner: NodeProcessRunner,
    ) -> ExecutionResult:
        from shell_ddd.domain.value_objects.execution_result import ExecutionResult
        from shell_ddd.domain.value_objects.manifest import Manifest
        from shell_ddd.domain.value_objects.mode import Mode

        manifest = Manifest(
            name=node_id,
            mode=Mode(self.mode),
            role=self.mode,  # fallback role = mode name
            node_type=self.mode,
            version="1",
        )
        return await runner.run(manifest, workspace_path)


# ---------------------------------------------------------------------------
# Concrete strategies
# ---------------------------------------------------------------------------

class AgentStrategy(_BaseStrategy):
    mode = "agent"


class RouterStrategy(_BaseStrategy):
    mode = "router"


class TaskerStrategy(_BaseStrategy):
    mode = "tasker"


class ToolStrategy(_BaseStrategy):
    mode = "tool"


class WorkerStrategy(_BaseStrategy):
    mode = "worker"


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_STRATEGY_MAP: dict[str, NodeExecutionStrategy] = {
    "agent": AgentStrategy(),
    "router": RouterStrategy(),
    "tasker": TaskerStrategy(),
    "tool": ToolStrategy(),
    "worker": WorkerStrategy(),
}


def get_strategy(mode: str) -> NodeExecutionStrategy:
    """Return the strategy for the given mode string.

    Raises InvalidNodeMode if the mode is unknown.
    """
    from shell_ddd.domain.exceptions import InvalidNodeMode

    strategy = _STRATEGY_MAP.get(mode)
    if strategy is None:
        raise InvalidNodeMode(f"Unknown node mode: {mode!r}")
    return strategy
```

### bootstrap/__init__.py
```
```

### bootstrap/container.py
```
"""ApplicationFactory — wires all handlers, ports, and adapters together."""
from __future__ import annotations

from dataclasses import dataclass

from shell_ddd.application.bus import CommandBus, EventBus, QueryBus
from shell_ddd.application.command_handlers.archive_envelope_handler import ArchiveEnvelopeHandler
from shell_ddd.application.command_handlers.bootstrap_runner_config_handler import (
    BootstrapRunnerConfigHandler,
)
from shell_ddd.application.command_handlers.import_task_handler import ImportTaskHandler
from shell_ddd.application.command_handlers.route_envelopes_handler import RouteEnvelopesHandler
from shell_ddd.application.command_handlers.run_node_handler import RunNodeHandler
from shell_ddd.application.command_handlers.run_tasker_workflow_handler import RunTaskerWorkflowHandler
from shell_ddd.application.command_handlers.save_node_result_handler import SaveNodeResultHandler
from shell_ddd.application.command_handlers.save_prompt_handler import SavePromptHandler
from shell_ddd.application.command_handlers.start_workflow_handler import StartWorkflowHandler
from shell_ddd.application.commands.commands import (
    ArchiveEnvelopeCommand,
    BootstrapRunnerConfigCommand,
    ImportTaskCommand,
    RouteEnvelopesCommand,
    RunNodeCommand,
    RunTaskerWorkflowCommand,
    SaveNodeResultCommand,
    SavePromptCommand,
    StartWorkflowCommand,
)
from shell_ddd.application.queries.queries import (
    GetCurrentTaskQuery,
    GetEnvelopesByWorkflowQuery,
    GetNodeResultQuery,
    GetPromptQuery,
    GetRunnerConfigQuery,
    GetTaskByNameQuery,
    GetWorkflowQuery,
)
from shell_ddd.application.query_handlers.query_handlers import (
    GetCurrentTaskHandler,
    GetEnvelopesByWorkflowHandler,
    GetNodeResultHandler,
    GetPromptHandler,
    GetRunnerConfigHandler,
    GetTaskByNameHandler,
    GetWorkflowHandler,
)
from shell_ddd.application.strategies.node_execution_strategy import get_strategy
from shell_ddd.infrastructure.logging.composite_event_publisher import CompositeEventPublisher
from shell_ddd.infrastructure.logging.logging_event_publisher import LoggingEventPublisher
from shell_ddd.infrastructure.logging.sql_audit_publisher import SqlAuditPublisher
from shell_ddd.infrastructure.logging.stdlib_logger import StdlibLogger
from shell_ddd.infrastructure.persistence import SqlAlchemyUnitOfWork
from shell_ddd.infrastructure.persistence.sql import build_session_factory, create_all_tables


@dataclass
class Container:
    """Assembled application container."""

    command_bus: CommandBus
    query_bus: QueryBus
    event_bus: EventBus


class ApplicationFactory:
    """Builds a Container for the given database URL.

    Supports:
    - ``sqlite+aiosqlite:///path/to/db``
    - ``postgresql+asyncpg://user:pass@host/db``
    """

    def __init__(self, database_url: str, max_step: int = 0) -> None:
        self._database_url = database_url
        self._max_step = max_step

    async def build(self) -> Container:
        """Initialise the DB schema (if needed) and wire all components."""
        await create_all_tables(self._database_url)
        session_factory = build_session_factory(self._database_url)

        from shell_ddd.infrastructure.persistence.memory.memory import (
            FakeClock,
            FakeIdGenerator,
            FakeTaskLoader,
        )

        # Concrete adapters
        uow = SqlAlchemyUnitOfWork(session_factory)
        clock = FakeClock.__new__(FakeClock)  # placeholder; replace with SystemClock below

        from shell_ddd.infrastructure.time.system_clock import SystemClock

        clock = SystemClock()
        id_gen = FakeIdGenerator()  # placeholder; real UUID generator below

        from shell_ddd.shared.ids import UuidIdGenerator

        id_gen = UuidIdGenerator()

        event_bus = EventBus()
        stdlib_logger = StdlibLogger("shell_ddd")
        event_publisher: CompositeEventPublisher = CompositeEventPublisher(
            [
                LoggingEventPublisher(stdlib_logger),
                SqlAuditPublisher(session_factory),
                _EventBusPublisher(event_bus),
            ]
        )

        task_loader = FakeTaskLoader()  # replaced by real FS loader when available

        # Build default node execution strategy (agent by default — CLI sets per node)
        strategy = get_strategy("agent")

        # Fake workspace / runner — replaced by real adapters in Faza 4
        from shell_ddd.infrastructure.persistence.memory.memory import FakeNodeProcessRunner, FakeNodeWorkspace  # noqa: F401

        workspace = FakeNodeWorkspace()
        runner = FakeNodeProcessRunner()

        # Command bus
        command_bus = CommandBus()
        command_bus.register(
            ImportTaskCommand,
            ImportTaskHandler(uow, clock, id_gen, task_loader, event_publisher),
        )
        command_bus.register(
            StartWorkflowCommand,
            StartWorkflowHandler(uow, clock, id_gen, event_publisher),
        )
        command_bus.register(
            RouteEnvelopesCommand,
            RouteEnvelopesHandler(uow, clock, event_publisher, self._max_step),
        )
        command_bus.register(
            RunNodeCommand,
            RunNodeHandler(uow, clock, id_gen, workspace, runner, strategy, event_publisher),
        )
        command_bus.register(
            ArchiveEnvelopeCommand,
            ArchiveEnvelopeHandler(uow, clock, event_publisher),
        )
        command_bus.register(
            SaveNodeResultCommand,
            SaveNodeResultHandler(uow, clock, id_gen, event_publisher),
        )
        command_bus.register(
            SavePromptCommand,
            SavePromptHandler(uow, clock, id_gen),
        )
        command_bus.register(
            BootstrapRunnerConfigCommand,
            BootstrapRunnerConfigHandler(uow, clock, id_gen),
        )
        command_bus.register(
            RunTaskerWorkflowCommand,
            RunTaskerWorkflowHandler(uow, clock, id_gen, runner, event_publisher),
        )

        # Query bus
        query_bus = QueryBus()
        query_bus.register(GetTaskByNameQuery, GetTaskByNameHandler(uow))
        query_bus.register(GetCurrentTaskQuery, GetCurrentTaskHandler(uow))
        query_bus.register(GetWorkflowQuery, GetWorkflowHandler(uow))
        query_bus.register(GetEnvelopesByWorkflowQuery, GetEnvelopesByWorkflowHandler(uow))
        query_bus.register(GetNodeResultQuery, GetNodeResultHandler(uow))
        query_bus.register(GetPromptQuery, GetPromptHandler(uow))
        query_bus.register(GetRunnerConfigQuery, GetRunnerConfigHandler(uow))

        return Container(
            command_bus=command_bus,
            query_bus=query_bus,
            event_bus=event_bus,
        )


class _EventBusPublisher:
    """Adapts EventBus to the EventPublisher port."""

    def __init__(self, bus: EventBus) -> None:
        self._bus = bus

    async def publish(self, events: list) -> None:
        await self._bus.publish(events)
```

### bootstrap/main.py
```
"""bootstrap/main.py — runnable module for smoke-testing and admin tasks.

Usage:
    python -m shell_ddd.bootstrap.main smoke [--db-url sqlite+aiosqlite:///smoke.db]
    python -m shell_ddd.bootstrap.main relay  [--db-url ...]  # process outbox once
"""
from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path


async def _smoke(db_url: str) -> None:
    """End-to-end smoke test: import → start-workflow → route.

    Uses an in-memory task (no real filesystem reads) so it runs without
    any external files.
    """
    from shell_ddd.application.commands.commands import (
        ImportTaskCommand,
        RouteEnvelopesCommand,
        StartWorkflowCommand,
    )
    from shell_ddd.application.queries.queries import GetWorkflowQuery
    from shell_ddd.bootstrap.container import ApplicationFactory

    print(f"[smoke] using database: {db_url}")
    container = await ApplicationFactory(database_url=db_url).build()
    bus = container.command_bus
    qbus = container.query_bus

    # --- 1. Write a minimal .md / .yaml to a temp dir and import the task ---
    with tempfile.TemporaryDirectory() as tmp:
        md = Path(tmp) / "smoke-task.md"
        md.write_text("# Smoke task\nThis is a smoke-test task.", encoding="utf-8")
        yaml = Path(tmp) / "smoke-task.yaml"
        yaml.write_text("graph:\n  nodes: []\n", encoding="utf-8")

        task_id = await bus.dispatch(
            ImportTaskCommand(
                md_path=str(md),
                yaml_path=str(yaml),
                task_name="smoke-task",
            )
        )
    print(f"[smoke] task imported: {task_id}")

    # --- 2. Start a workflow ---
    workflow_id = await bus.dispatch(
        StartWorkflowCommand(task_name="smoke-task")
    )
    print(f"[smoke] workflow started: {workflow_id}")

    # --- 3. Route (0 envelopes expected for empty graph) ---
    routed = await bus.dispatch(
        RouteEnvelopesCommand(workflow_id=workflow_id)
    )
    print(f"[smoke] envelopes routed: {routed}")

    # --- 4. Query workflow status ---
    dto = await qbus.dispatch(GetWorkflowQuery(workflow_id))
    print(f"[smoke] workflow status: {dto.status if dto else 'not found'}")
    print("[smoke] OK")


async def _relay(db_url: str) -> None:
    """Process one batch of pending outbox events."""
    from shell_ddd.infrastructure.logging.composite_event_publisher import CompositeEventPublisher
    from shell_ddd.infrastructure.logging.logging_event_publisher import LoggingEventPublisher
    from shell_ddd.infrastructure.logging.stdlib_logger import StdlibLogger
    from shell_ddd.infrastructure.messaging.outbox_relay import OutboxRelay
    from shell_ddd.infrastructure.persistence.sql import build_session_factory, create_all_tables

    await create_all_tables(db_url)
    sf = build_session_factory(db_url)
    logger = StdlibLogger("shell_ddd.relay")
    downstream = CompositeEventPublisher([LoggingEventPublisher(logger)])
    relay = OutboxRelay(sf, downstream)
    count = await relay.run_once()
    print(f"[relay] processed {count} outbox event(s)")


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: python -m shell_ddd.bootstrap.main <command> [--db-url URL]")
        print("  smoke  — import→workflow→route end-to-end check")
        print("  relay  — process one batch of outbox events")
        return 0

    cmd = args[0]
    db_url = "sqlite+aiosqlite:///shell_ddd.db"
    for i, a in enumerate(args[1:], 1):
        if a == "--db-url" and i + 1 < len(args):
            db_url = args[i + 1]

    if cmd == "smoke":
        asyncio.run(_smoke(db_url))
        return 0
    elif cmd == "relay":
        asyncio.run(_relay(db_url))
        return 0
    else:
        print(f"Unknown command: {cmd!r}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

### docker-compose.test.yml
```
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: shell_test
      POSTGRES_PASSWORD: shell_test
      POSTGRES_DB: shell_test
    ports:
      - "5433:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U shell_test"]
      interval: 5s
      timeout: 5s
      retries: 5

  mongo:
    image: mongo:7
    command: ["mongod", "--replSet", "rs0", "--bind_ip_all"]
    ports:
      - "27018:27017"
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping').ok", "--quiet"]
      interval: 5s
      timeout: 5s
      retries: 10
    entrypoint: >
      bash -c "
        mongod --replSet rs0 --bind_ip_all &
        until mongosh --eval 'db.adminCommand(\"ping\").ok' --quiet; do sleep 1; done;
        mongosh --eval 'rs.initiate({_id:\"rs0\",members:[{_id:0,host:\"localhost:27017\"}]})';
        wait
      "
```

### docs/adr/ADR-0001_single_bounded_context.md
```
# ADR-0001: Single Bounded Context `shell`

**Date:** 2025-01  
**Status:** Accepted

## Context

The SHELL platform has five execution modes: `agent`, `router`, `tasker`, `tool`, `worker`.  
An initial design question was whether to split these into separate bounded contexts.

## Decision

All five modes live inside one bounded context named `shell`.  
They are modelled as **execution strategies** (`NodeExecutionStrategy` port + 5 implementations)
within the `application/strategies/` layer, not as separate modules or microservices.

## Rationale

1. Modes share almost all domain concepts: `Task`, `Workflow`, `Envelope`, `NodeState`, `Graph`.  
   Splitting them would require cross-context event choreography for what are today in-process calls.
2. Each mode is a *variant of the same lifecycle* (receive envelope → execute → emit result).  
   A Strategy pattern captures this without over-engineering.
3. The platform is deployed as a single process; splitting BCs would add latency without benefit.

## Consequences

- One `UnitOfWork`, one set of SQL tables, one `ApplicationFactory`.
- New mode variants add a `*Strategy` class without touching domain or ports.
- If the platform later splits into microservices, each mode can be promoted to its own BC with
  defined anti-corruption layers.
```

### docs/adr/ADR-0002_strategies_over_modules.md
```
# ADR-0002: Execution Modes as Application Strategies

**Date:** 2025-01  
**Status:** Accepted

## Context

The original SHELL architecture had five independent top-level packages (`agent/`, `router/`,
`tasker/`, `tool/`, `worker/`), each with its own `entrypoint.py` and deep module hierarchies.

## Decision

In `shell_ddd`, the five modes become **Strategy implementations** of the
`NodeExecutionStrategy` port defined in `application/ports/`.  
The CLI dispatches to the right strategy via `ApplicationFactory.get_strategy(mode)`.

## Rationale

1. Duplication: all five modes share ~80 % of their logic (envelope lifecycle, task loading, result
   persistence). Strategies share this through shared handlers.
2. The old pattern (separate packages with internal `_init_*.py` per feature) scattered logic that
   belongs in one place and made cross-cutting concerns (logging, correlation) hard to apply
   uniformly.
3. Strategies are easily testable in isolation with `InMemory*` adapters and `FakeNodeProcessRunner`.

## Consequences

- New modes: add `*Strategy` class + register in `bootstrap/container.py`.
- Old `agent/`, `router/`, etc. entrypoints remain as thin shims (CLI parity requirement).
- The `NodeExecutionStrategy` port is the only point of extension for execution behaviour.
```

### docs/adr/ADR-0003_sql_adapters.md
```
# ADR-0003: Shared SQL Adapters for SQLite and PostgreSQL

**Date:** 2025-01  
**Status:** Accepted

## Context

The old SHELL had two separate SQL drivers (`SqliteDriver`, `PostgresDriver`) that duplicated
repository code.  The new design must support both dialects without duplication.

## Decision

`shell_ddd` uses a **single set of SQLAlchemy 2.x async ORM models and repositories** located in
`infrastructure/persistence/sql/`.  Dialect is selected at runtime by the `database_url` string:

- `sqlite+aiosqlite://...` → aiosqlite engine
- `postgresql+asyncpg://...` → asyncpg engine

The `build_session_factory(url)` helper in `infrastructure/persistence/sql/__init__.py`
creates the correct `AsyncEngine` and returns an `async_sessionmaker`.

## Rationale

1. SQLAlchemy abstracts dialect differences at the ORM level; column types like `JSON` work on both.
2. Dialect-specific Alembic migration scripts live in `migrations/sql/versions/` and use
   `op.get_context().dialect.name` for any per-dialect DDL differences.
3. PostgreSQL uses `asyncpg`; SQLite uses `aiosqlite` — both are async-native, matching the
   fully-async application layer.

## Consequences

- Adding a new DB column requires one Alembic migration that covers both dialects.
- MongoDB is a separate adapter tree (`infrastructure/persistence/mongo/`) and is not shared.
- Tests run against SQLite by default; CI optionally starts Postgres+Mongo via `docker-compose.test.yml`.
```

### docs/dokumentacja/doc.md
```
[ Klient / Testy / API ]
│
▼
┌────────────────────────────────────────────────────────┐
│ WARSTWA INFRASTRUKTURY WEJŚCIOWEJ                      │
│ - Tworzy: Command / Query (DTO)                        │
│ - Wywołuje: CommandBus.dispatch() / QueryBus.dispatch()│
└───────────────────────┬────────────────────────────────┘
│
▼
┌────────────────────────────────────────────────────────┐
│ WARSTWA APLIKACJI (Buses & Handlers)                   │
│ - Szyny (CommandBus, QueryBus) przekazują paczkę do:   │
│   -> CommandHandler (np. StartWorkflowHandler)         │
└───────────────────────┬────────────────────────────────┘
│
├──────────────────────────────────────────┐
▼ (używa portów / interfejsów)             ▼ (zapisuje eventy)
┌──────────────────────────────────────────┐   ┌─────────────────────────────────────┐
│ PORTY APLIKACJI (Interfejsy)             │   │ PORT EVENTÓW                        │
│ - UnitOfWork (Abstract)                  │   │ - EventPublisher (Abstract)         │
└───────────────────────┬──────────────────┘   └───────────────────┬─────────────────┘
│                                          │
▼ (konkretna implementacja)                ▼ (konkretna implementacja)
┌──────────────────────────────────────────┐   ┌─────────────────────────────────────┐
│ ADAPTERY INFRASTRUKTURY                  │   │ ADAPTER TRANSMISJI                  │
│ - SqlAlchemyUnitOfWork                   │   │ - SqlOutboxPublisher                │
│   (Zarządza AsyncSession)                │   │   (Zapisuje do OutboxEventModel)    │
│ - SqlPromptRepository, etc.              │   └─────────────────────────────────────┘
└───────────────────────┬──────────────────┘
│
▼ (ładuje / zapisuje)
┌────────────────────────────────────────────────────────┐
│ WARSTWA DOMENY (Jądro systemu)                         │
│ - Agregaty & Encje (Envelope, Prompt, Task)           │
│ - Logika biznesowa, niezmienniki, reguły stanów        │
└────────────────────────────────────────────────────────┘


🔄 Szczegółowy podział na warstwy i relacje klas
1. Wejście do systemu (Infrastruktura aplikacyjna)
   Klasy: TestSqlCommitRollback, StartWorkflowCommand, GetPromptQuery.

Przepływ: Zewnętrzny świat (np. test integracyjny lub kontroler API) tworzy niemutowalny obiekt intencji (Command lub Query) 
i wrzuca go do odpowiedniej szyny (CommandBus/QueryBus).

Zależność: Warstwa ta zależy wyłącznie od interfejsu szyny oraz struktur DTO/Commands.

2. Warstwa Orkiestracji (Aplikacja / Handlery)
   Klasy: CommandBus, QueryBus, StartWorkflowHandler, SaveNodeResultHandler.

Przepływ: CommandBus znajduje w słowniku _handlers odpowiednią klasę handlera i wywołuje metodę handle(command).

Zależność: Handlery implementują logikę aplikacyjną. Nie wykonują operacji na bazie danych bezpośrednio – w swoim konstruktorze 
przyjmują abstrakcję UnitOfWork (Dependency Injection).

3. Warstwa Dostępu do Danych (Adaptery Infrastruktury)
   Klasy: SqlAlchemyUnitOfWork, SqlPromptRepository, SqlEnvelopeRepository.

Przepływ: 1. Handler otwiera kontekst menedżera: async with self._uow as uow:.
2. SqlAlchemyUnitOfWork tworzy sesję SQLAlchemy (AsyncSession).
3. Handler poprzez uow.prompts lub uow.envelopes wywołuje metody repozytorium (np. save(), get_by_id()).

Zależność: Klasy repozytoriów zależą od modeli SQLAlchemy (OutboxEventModel, etc.), ale mapują je na czyste obiekty domenowe.

4. Serce Biznesowe (Czysta Domena)
   Klasy: Envelope, Prompt, Task, TaskId, Status.

Przepływ: Repozytorium wyciąga surowe dane z bazy, rekonstruuje z nich obiekt domenowy (np. Envelope) 
i przekazuje go do Handlera. Handler wywołuje na encji metodę biznesową (np. zmianę stanu, walidację).
Encja modyfikuje swój stan wewnętrzny i opcjonalnie generuje zdarzenie (np. WorkflowStarted).

Zależność: Brak zależności zewnętrznych. Domena stoi na samym dole hierarchii. Klasy takie jak TaskId czy Status to 
Value Objects wykorzystywane przez Encje.

5. Asynchroniczny przepływ zdarzeń (Wzorzec Outbox)
   W Twoim kodzie zastosowano genialne oddzielenie efektów ubocznych za pomocą bazy danych:

Plaintext

[Handler / Domena] ──(Generuje DomainEvent)──> [SqlOutboxPublisher] ──> Zapis w DB (outbox_event)
│
(Asynchroniczny proces)
▼
[Klient końcowy] <── [EventBus] <── [EventPublisher] <── [_OutboxProxy] <── [OutboxRelay]

Krok A: Handler po udanej operacji biznesowej przekazuje zdarzenia domenowe do SqlOutboxPublisher.

Krok B: SqlOutboxPublisher tworzy dedykowaną, krótką sesję DB i zapisuje wiersz w tabeli outbox_event jako 
JSON (dzięki temu nawet jeśli transakcja główna się wycofa, ślad o błędzie lub zdarzeniu technicznym może zostać utrwalony, bądź – przy pełnym UoW – zostanie zatwierdzony razem z domeną).

Krok C: OutboxRelay działa w tle. Cyklicznie odpytuje tabelę OutboxEventModel o nieopublikowane wiersze (published_at.is_(None)). 
Wrapuje je w lekkie obiekty _OutboxProxy i przekazuje do właściwego, pamięciowego EventBus, który powiadamia asynchronicznych odbiorców (Event Handlerów).

💡 Kluczowy wniosek architektoniczny
Wszystkie strzałki zależności kompilacji (kto importuje kogo) skierowane są w stronę domeny. Kod infrastruktury bazy danych 
(sql/models.py) implementuje interfejsy zdefiniowane w domenie/aplikacji. Dzięki temu rozwiązaniu, zmiana bazy danych z SQLite/PostgreSQL
na np. MongoDB wymagałaby jedynie napisania nowego adaptera (klasy implementującej porty repozytoriów), podczas gdy cała logika 
w handlerach i encjach pozostałaby nienaruszona.
```

### domain/__init__.py
```
```

### domain/entities/__init__.py
```
```

### domain/entities/envelope.py
```
"""Envelope aggregate with embedded EnvelopeEvents."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell_ddd.domain.exceptions import InvalidEnvelopeTransition
from shell_ddd.domain.value_objects.envelope_status import EnvelopeStage, EnvelopeStatus

if TYPE_CHECKING:
    from shell_ddd.domain.value_objects.ids import EnvelopeId, NodeId, WorkflowId


@dataclass(slots=True)
class EnvelopeEvent:
    kind: str
    payload: dict[str, object]
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))


# Allowed status transitions
_STATUS_TRANSITIONS: dict[EnvelopeStatus, set[EnvelopeStatus]] = {
    EnvelopeStatus.PENDING: {EnvelopeStatus.ACTIVE, EnvelopeStatus.DEAD},
    EnvelopeStatus.ACTIVE: {EnvelopeStatus.DELIVERED, EnvelopeStatus.FAILED},
    EnvelopeStatus.DELIVERED: {EnvelopeStatus.ARCHIVED} if False else set(),
    EnvelopeStatus.FAILED: {EnvelopeStatus.PENDING, EnvelopeStatus.DEAD},
    EnvelopeStatus.DEAD: set(),
}

_STATUS_TRANSITIONS = {
    EnvelopeStatus.PENDING: {EnvelopeStatus.ACTIVE, EnvelopeStatus.DEAD},
    EnvelopeStatus.ACTIVE: {EnvelopeStatus.DELIVERED, EnvelopeStatus.FAILED},
    EnvelopeStatus.DELIVERED: set(),
    EnvelopeStatus.FAILED: {EnvelopeStatus.PENDING, EnvelopeStatus.DEAD},
    EnvelopeStatus.DEAD: set(),
}


@dataclass(slots=True)
class Envelope:
    """Envelope aggregate root."""

    id: EnvelopeId
    workflow_id: WorkflowId
    parent_id: EnvelopeId | None
    correlation_id: str
    sender_node_id: NodeId
    receiver_node_id: NodeId
    source_role: str
    target_role: str
    sequence_id: int
    step: int
    status: EnvelopeStatus
    stage: EnvelopeStage
    payload: dict[str, object]
    artifact_uri: str
    archive_uri: str
    created_at: datetime
    updated_at: datetime
    events: list[EnvelopeEvent] = field(default_factory=list)

    @classmethod
    def new(
        cls,
        *,
        id_: EnvelopeId,
        workflow_id: WorkflowId,
        sender_node_id: NodeId,
        receiver_node_id: NodeId,
        source_role: str,
        target_role: str,
        correlation_id: str = "",
        parent_id: EnvelopeId | None = None,
        sequence_id: int = 0,
        step: int = 0,
        payload: dict[str, object] | None = None,
        now: datetime | None = None,
    ) -> Envelope:
        ts = now or datetime.now(tz=UTC)
        return cls(
            id=id_,
            workflow_id=workflow_id,
            parent_id=parent_id,
            correlation_id=correlation_id or str(id_),
            sender_node_id=sender_node_id,
            receiver_node_id=receiver_node_id,
            source_role=source_role,
            target_role=target_role,
            sequence_id=sequence_id,
            step=step,
            status=EnvelopeStatus.PENDING,
            stage=EnvelopeStage.DRAFT,
            payload=payload or {},
            artifact_uri="",
            archive_uri="",
            created_at=ts,
            updated_at=ts,
        )

    def transition_status(self, new_status: EnvelopeStatus, now: datetime | None = None) -> None:
        allowed = _STATUS_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise InvalidEnvelopeTransition(
                f"Cannot transition envelope {self.id.value!r} "
                f"from {self.status.value!r} to {new_status.value!r}"
            )
        self.status = new_status
        self.updated_at = now or datetime.now(tz=UTC)
        self.events.append(
            EnvelopeEvent(kind="status_changed", payload={"status": new_status.value})
        )

    def transition_stage(self, new_stage: EnvelopeStage, now: datetime | None = None) -> None:
        self.stage = new_stage
        self.updated_at = now or datetime.now(tz=UTC)
```

### domain/entities/node.py
```
"""Node entity — lightweight model of a running node instance."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell_ddd.domain.value_objects.ids import NodeId
    from shell_ddd.domain.value_objects.mode import Mode


@dataclass(slots=True)
class Node:
    """Represents a running node instance (not a graph definition node)."""

    id: NodeId
    mode: Mode
    role: str
    node_type: str
    workspace_path: str  # opaque str, resolved by NodeWorkspace in infrastructure
```

### domain/entities/node_result.py
```
"""NodeResult aggregate."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell_ddd.domain.value_objects.ids import NodeId, NodeResultId, WorkflowId
    from shell_ddd.domain.value_objects.status import Status


@dataclass(slots=True)
class NodeResult:
    id: NodeResultId
    node_id: NodeId
    workflow_id: WorkflowId
    status: Status
    stdout: str
    stderr: str
    artifact_uri: str
    created_at: datetime

    @classmethod
    def new(
        cls,
        *,
        id_: NodeResultId,
        node_id: NodeId,
        workflow_id: WorkflowId,
        status: Status,
        stdout: str = "",
        stderr: str = "",
        artifact_uri: str = "",
        now: datetime | None = None,
    ) -> NodeResult:
        return cls(
            id=id_,
            node_id=node_id,
            workflow_id=workflow_id,
            status=status,
            stdout=stdout,
            stderr=stderr,
            artifact_uri=artifact_uri,
            created_at=now or datetime.now(tz=UTC),
        )
```

### domain/entities/prompt.py
```
"""Prompt aggregate."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell_ddd.domain.value_objects.hash import Hash

if TYPE_CHECKING:
    from shell_ddd.domain.value_objects.ids import PromptId


@dataclass(slots=True)
class Prompt:
    id: PromptId
    name: str
    version: int
    hash: Hash
    body: str
    source_uri: str
    is_current: bool
    created_at: datetime

    @classmethod
    def new(
        cls,
        *,
        id_: PromptId,
        name: str,
        body: str,
        source_uri: str = "",
        now: datetime | None = None,
    ) -> Prompt:
        return cls(
            id=id_,
            name=name,
            version=1,
            hash=Hash.of(body),
            body=body,
            source_uri=source_uri,
            is_current=True,
            created_at=now or datetime.now(tz=UTC),
        )
```

### domain/entities/rag_document.py
```
"""RagDocument — aggregate root for an indexed document and its chunks."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from shell_ddd.domain.value_objects.ids import RagChunkId, RagDocumentId


@dataclass(frozen=True, slots=True)
class RagChunk:
    id: RagChunkId
    document_id: RagDocumentId
    chunk_index: int
    chunk_text: str
    embedding: bytes          # raw little-endian float32 blob
    embedding_model: str

    def __post_init__(self) -> None:
        if self.chunk_index < 0:
            raise ValueError("chunk_index must be >= 0")
        if not self.chunk_text:
            raise ValueError("chunk_text cannot be empty")
        if not self.embedding_model:
            raise ValueError("embedding_model cannot be empty")


@dataclass(slots=True)
class RagDocument:
    id: RagDocumentId
    source_uri: str
    title: str
    domain: str
    created_at: datetime
    chunks: list[RagChunk] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.source_uri:
            raise ValueError("source_uri cannot be empty")
        if not self.title:
            raise ValueError("title cannot be empty")
        if not self.domain:
            raise ValueError("domain cannot be empty")

    @classmethod
    def new(
        cls,
        id_: RagDocumentId,
        source_uri: str,
        title: str,
        domain: str,
        now: datetime,
    ) -> RagDocument:
        return cls(
            id=id_,
            source_uri=source_uri,
            title=title,
            domain=domain,
            created_at=now,
        )

    def add_chunks(
        self,
        chunk_ids: list[RagChunkId],
        texts: list[str],
        embeddings: list[bytes],
        model: str,
    ) -> None:
        if not (len(chunk_ids) == len(texts) == len(embeddings)):
            raise ValueError("chunk_ids, texts and embeddings must have equal length")
        for i, (cid, text, emb) in enumerate(zip(chunk_ids, texts, embeddings)):
            self.chunks.append(
                RagChunk(
                    id=cid,
                    document_id=self.id,
                    chunk_index=i,
                    chunk_text=text,
                    embedding=emb,
                    embedding_model=model,
                )
            )
```

### domain/entities/runner_config.py
```
"""RunnerConfig aggregate — serialized runner/module configuration."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell_ddd.domain.value_objects.hash import Hash

if TYPE_CHECKING:
    from shell_ddd.domain.value_objects.ids import RunnerConfigId


@dataclass(slots=True)
class RunnerConfig:
    id: RunnerConfigId
    package_name: str
    kind: str
    hash: Hash
    body: dict[str, object]
    created_at: datetime

    @classmethod
    def new(
        cls,
        *,
        id_: RunnerConfigId,
        package_name: str,
        kind: str,
        body: dict[str, object],
        now: datetime | None = None,
    ) -> RunnerConfig:
        import json

        serialized = json.dumps(body, sort_keys=True)
        return cls(
            id=id_,
            package_name=package_name,
            kind=kind,
            hash=Hash.of(serialized),
            body=body,
            created_at=now or datetime.now(tz=UTC),
        )
```

### domain/entities/session.py
```
"""Session + Message — conversation session aggregate."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from shell_ddd.domain.value_objects.ids import MessageId, SessionId


@dataclass(frozen=True, slots=True)
class Message:
    id: MessageId
    session_id: SessionId
    sender: str
    receiver: str
    payload: dict  # type: ignore[type-arg]
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.sender:
            raise ValueError("sender cannot be empty")
        if not self.receiver:
            raise ValueError("receiver cannot be empty")


@dataclass(slots=True)
class Session:
    id: SessionId
    agent_id: str
    goal: str
    status: str               # "open" | "closed"
    opened_at: datetime
    closed_at: datetime | None
    messages: list[Message] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.agent_id:
            raise ValueError("agent_id cannot be empty")
        if not self.goal:
            raise ValueError("goal cannot be empty")
        if self.status not in ("open", "closed"):
            raise ValueError(f"invalid status: {self.status!r}")

    @classmethod
    def open(
        cls,
        id_: SessionId,
        agent_id: str,
        goal: str,
        now: datetime,
    ) -> Session:
        return cls(
            id=id_,
            agent_id=agent_id,
            goal=goal,
            status="open",
            opened_at=now,
            closed_at=None,
        )

    def close(self, now: datetime) -> None:
        if self.status == "closed":
            raise ValueError("Session already closed")
        self.status = "closed"
        self.closed_at = now

    def append_message(
        self,
        msg_id: MessageId,
        sender: str,
        receiver: str,
        payload: dict,  # type: ignore[type-arg]
        now: datetime,
    ) -> Message:
        if self.status != "open":
            raise ValueError("Cannot append message to a closed session")
        msg = Message(
            id=msg_id,
            session_id=self.id,
            sender=sender,
            receiver=receiver,
            payload=payload,
            created_at=now,
        )
        self.messages.append(msg)
        return msg
```

### domain/entities/task.py
```
"""Task aggregate root with embedded Graph and GraphNodes."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell_ddd.domain.value_objects.hash import Hash

if TYPE_CHECKING:
    from shell_ddd.domain.value_objects.ids import GraphId, NodeId, TaskId
    from shell_ddd.domain.value_objects.mode import Mode
    from shell_ddd.domain.value_objects.task_name import TaskName


@dataclass(slots=True)
class GraphNode:
    """A single node definition within a Task's graph."""

    id: NodeId
    position: int
    node_dir: str
    mode: Mode
    role: str
    node_type: str
    model: str = ""
    command: str = ""
    timeout: int = 0
    retries: int = 0
    log_level: str = "INFO"
    max_step: int = 0
    no_ask_user: bool = False
    autopilot: bool = False
    task_name: str = ""
    source_dir: str = ""
    work_dir: str = ""
    status_initial: str = ""
    extra: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class Graph:
    """Graph embedded in a Task aggregate."""

    id: GraphId
    task_id: TaskId
    raw_dict: dict[str, object]
    nodes: list[GraphNode] = field(default_factory=list)


@dataclass(slots=True)
class Task:
    """Task aggregate root."""

    id: TaskId
    name: TaskName
    version: int
    hash: Hash
    body_md: str
    body_yaml_raw: str
    is_current: bool
    created_at: datetime
    graph: Graph | None = None

    @classmethod
    def new(
        cls,
        *,
        id_: TaskId,
        name: TaskName,
        body_md: str,
        body_yaml_raw: str,
        now: datetime | None = None,
    ) -> Task:
        created = now or datetime.now(tz=UTC)
        content_hash = Hash.of(body_md + body_yaml_raw)
        return cls(
            id=id_,
            name=name,
            version=1,
            hash=content_hash,
            body_md=body_md,
            body_yaml_raw=body_yaml_raw,
            is_current=True,
            created_at=created,
        )
```

### domain/entities/workflow.py
```
"""Workflow aggregate with embedded NodeStates."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell_ddd.domain.value_objects.status import Status

if TYPE_CHECKING:
    from shell_ddd.domain.value_objects.ids import NodeId, WorkflowId


@dataclass(slots=True)
class NodeState:
    node_id: NodeId
    status: Status
    step: int = 0
    updated_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))


@dataclass(slots=True)
class Workflow:
    """Workflow aggregate root."""

    id: WorkflowId
    task_name: str
    status: Status
    created_at: datetime
    node_states: dict[str, NodeState] = field(default_factory=dict)

    @classmethod
    def new(
        cls,
        *,
        id_: WorkflowId,
        task_name: str,
        now: datetime | None = None,
    ) -> Workflow:
        created = now or datetime.now(tz=UTC)
        return cls(
            id=id_,
            task_name=task_name,
            status=Status.idle(),
            created_at=created,
        )

    def start(self, now: datetime | None = None) -> None:
        self.status = Status.running()

    def complete(self) -> None:
        self.status = Status.done()

    def fail(self) -> None:
        self.status = Status.failed()

    def update_node_state(self, node_id: NodeId, status: Status, step: int = 0) -> None:
        self.node_states[node_id.value] = NodeState(
            node_id=node_id,
            status=status,
            step=step,
        )
```

### domain/events/__init__.py
```
```

### domain/events/events.py
```
"""Domain events for shell_ddd."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell_ddd.domain.value_objects.ids import (
        EnvelopeId,
        NodeId,
        NodeResultId,
        TaskId,
        WorkflowId,
    )
    from shell_ddd.domain.value_objects.task_name import TaskName


@dataclass(frozen=True, slots=True)
class DomainEvent:
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class TaskImported(DomainEvent):
    task_id: TaskId
    task_name: TaskName

    @classmethod
    def now(cls, task_id: TaskId, task_name: TaskName) -> TaskImported:
        return cls(
            occurred_at=datetime.now(tz=UTC),
            task_id=task_id,
            task_name=task_name,
        )


@dataclass(frozen=True, slots=True)
class WorkflowStarted(DomainEvent):
    workflow_id: WorkflowId
    task_name: str

    @classmethod
    def now(cls, workflow_id: WorkflowId, task_name: str) -> WorkflowStarted:
        return cls(
            occurred_at=datetime.now(tz=UTC),
            workflow_id=workflow_id,
            task_name=task_name,
        )


@dataclass(frozen=True, slots=True)
class EnvelopeRouted(DomainEvent):
    envelope_id: EnvelopeId
    workflow_id: WorkflowId

    @classmethod
    def now(cls, envelope_id: EnvelopeId, workflow_id: WorkflowId) -> EnvelopeRouted:
        return cls(
            occurred_at=datetime.now(tz=UTC),
            envelope_id=envelope_id,
            workflow_id=workflow_id,
        )


@dataclass(frozen=True, slots=True)
class EnvelopeExpired(DomainEvent):
    envelope_id: EnvelopeId
    workflow_id: WorkflowId

    @classmethod
    def now(cls, envelope_id: EnvelopeId, workflow_id: WorkflowId) -> EnvelopeExpired:
        return cls(
            occurred_at=datetime.now(tz=UTC),
            envelope_id=envelope_id,
            workflow_id=workflow_id,
        )


@dataclass(frozen=True, slots=True)
class NodeCompleted(DomainEvent):
    node_id: NodeId
    workflow_id: WorkflowId
    result_id: NodeResultId

    @classmethod
    def now(
        cls, node_id: NodeId, workflow_id: WorkflowId, result_id: NodeResultId
    ) -> NodeCompleted:
        return cls(
            occurred_at=datetime.now(tz=UTC),
            node_id=node_id,
            workflow_id=workflow_id,
            result_id=result_id,
        )


@dataclass(frozen=True, slots=True)
class NodeFailed(DomainEvent):
    node_id: NodeId
    workflow_id: WorkflowId
    reason: str

    @classmethod
    def now(cls, node_id: NodeId, workflow_id: WorkflowId, reason: str) -> NodeFailed:
        return cls(
            occurred_at=datetime.now(tz=UTC),
            node_id=node_id,
            workflow_id=workflow_id,
            reason=reason,
        )


@dataclass(frozen=True, slots=True)
class WorkflowCompleted(DomainEvent):
    workflow_id: WorkflowId
    task_name: str

    @classmethod
    def now(cls, workflow_id: WorkflowId, task_name: str) -> WorkflowCompleted:
        return cls(
            occurred_at=datetime.now(tz=UTC),
            workflow_id=workflow_id,
            task_name=task_name,
        )


@dataclass(frozen=True, slots=True)
class WorkflowFailed(DomainEvent):
    workflow_id: WorkflowId
    task_name: str

    @classmethod
    def now(cls, workflow_id: WorkflowId, task_name: str) -> WorkflowFailed:
        return cls(
            occurred_at=datetime.now(tz=UTC),
            workflow_id=workflow_id,
            task_name=task_name,
        )
```

### domain/exceptions.py
```
"""Domain exceptions for shell_ddd."""
from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain errors."""


class TaskNotFound(DomainError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Task not found: {name!r}")


class WorkflowNotFound(DomainError):
    def __init__(self, workflow_id: str) -> None:
        super().__init__(f"Workflow not found: {workflow_id!r}")


class EnvelopeNotFound(DomainError):
    def __init__(self, envelope_id: str) -> None:
        super().__init__(f"Envelope not found: {envelope_id!r}")


class InvalidTaskDefinition(DomainError):
    """Raised when task markdown/yaml has invalid structure."""


class InvalidEnvelopeTransition(DomainError):
    """Raised when envelope status/stage transition is forbidden."""


class NodeNotFound(DomainError):
    def __init__(self, node_id: str) -> None:
        super().__init__(f"Node not found: {node_id!r}")


class PromptNotFound(DomainError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Prompt not found: {name!r}")


class RunnerConfigNotFound(DomainError):
    def __init__(self, package_name: str) -> None:
        super().__init__(f"RunnerConfig not found: {package_name!r}")


class RoleNotResolvable(DomainError):
    """Raised when no graph node satisfies the requested role."""


class MaxStepExceeded(DomainError):
    """Raised when envelope step >= max_step TTL."""


class InvalidNodeMode(DomainError):
    """Raised when an unknown node mode is encountered."""
```

### domain/repositories/__init__.py
```
```

### domain/repositories/repositories.py
```
"""Repository port interfaces (domain-level)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell_ddd.domain.entities.envelope import Envelope
    from shell_ddd.domain.entities.node_result import NodeResult
    from shell_ddd.domain.entities.prompt import Prompt
    from shell_ddd.domain.entities.rag_document import RagChunk, RagDocument
    from shell_ddd.domain.entities.runner_config import RunnerConfig
    from shell_ddd.domain.entities.session import Message, Session
    from shell_ddd.domain.entities.task import Task
    from shell_ddd.domain.entities.workflow import Workflow
    from shell_ddd.domain.value_objects.ids import (
        EnvelopeId,
        MessageId,
        NodeId,
        NodeResultId,
        PromptId,
        RagDocumentId,
        RunnerConfigId,
        SessionId,
        TaskId,
        WorkflowId,
    )
    from shell_ddd.domain.value_objects.task_name import TaskName


class TaskRepository(Protocol):
    async def get_by_id(self, task_id: TaskId) -> Task | None: ...
    async def get_by_name(self, name: TaskName) -> Task | None: ...
    async def get_current_by_name(self, name: TaskName) -> Task | None: ...
    async def save(self, task: Task) -> None: ...
    async def list_current(self) -> list[Task]: ...


class WorkflowRepository(Protocol):
    async def get_by_id(self, workflow_id: WorkflowId) -> Workflow | None: ...
    async def save(self, workflow: Workflow) -> None: ...


class EnvelopeRepository(Protocol):
    async def get_by_id(self, envelope_id: EnvelopeId) -> Envelope | None: ...
    async def save(self, envelope: Envelope) -> None: ...
    async def list_by_workflow(self, workflow_id: WorkflowId) -> list[Envelope]: ...
    async def list_pending(self, workflow_id: WorkflowId) -> list[Envelope]: ...


class EnvelopeArchive(Protocol):
    async def archive(self, envelope: Envelope) -> str: ...  # returns archive_uri
    async def get(self, archive_uri: str) -> Envelope | None: ...


class PromptRepository(Protocol):
    async def get_by_id(self, prompt_id: PromptId) -> Prompt | None: ...
    async def get_current_by_name(self, name: str) -> Prompt | None: ...
    async def save(self, prompt: Prompt) -> None: ...


class NodeResultRepository(Protocol):
    async def get_by_id(self, result_id: NodeResultId) -> NodeResult | None: ...
    async def get_by_node_and_workflow(
        self, node_id: NodeId, workflow_id: WorkflowId
    ) -> NodeResult | None: ...
    async def save(self, result: NodeResult) -> None: ...


class RunnerConfigRepository(Protocol):
    async def get_by_id(self, config_id: RunnerConfigId) -> RunnerConfig | None: ...
    async def get_by_package(self, package_name: str) -> RunnerConfig | None: ...
    async def save(self, config: RunnerConfig) -> None: ...


class RagDocumentRepository(Protocol):
    async def save(self, document: RagDocument) -> None: ...
    async def get_by_id(self, doc_id: RagDocumentId) -> RagDocument | None: ...
    async def search_similar(
        self,
        query_embedding: bytes,
        top_k: int = 5,
        domain: str | None = None,
    ) -> list[RagChunk]: ...


class SessionRepository(Protocol):
    async def save(self, session: Session) -> None: ...
    async def get_by_id(self, session_id: SessionId) -> Session | None: ...
    async def get_messages(self, session_id: SessionId) -> list[Message]: ...
```

### domain/services/__init__.py
```
```

### domain/services/envelope_lifecycle_service.py
```
"""EnvelopeLifecycleService — pure domain TTL/expiry logic."""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell_ddd.domain.value_objects.envelope_status import EnvelopeStatus

if TYPE_CHECKING:
    from shell_ddd.domain.entities.envelope import Envelope


class EnvelopeLifecycleService:
    """Determines whether an envelope should be expired based on step count."""

    @staticmethod
    def should_expire(envelope: Envelope, max_step: int) -> bool:
        """Return True if envelope has exceeded the max_step TTL."""
        if max_step <= 0:
            return False
        return envelope.step >= max_step

    @staticmethod
    def advance(envelope: Envelope, max_step: int) -> EnvelopeStatus:
        """Return the new status after considering TTL.

        - If step >= max_step → DEAD
        - Else keep current status.
        """
        if EnvelopeLifecycleService.should_expire(envelope, max_step):
            return EnvelopeStatus.DEAD
        return envelope.status
```

### domain/services/graph_routing_service.py
```
"""GraphRoutingService — pure domain routing logic."""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell_ddd.domain.exceptions import RoleNotResolvable

if TYPE_CHECKING:
    from shell_ddd.domain.entities.task import Graph, GraphNode
    from shell_ddd.domain.value_objects.ids import NodeId


class GraphRoutingService:
    """Resolves target_role -> NodeId using the task graph."""

    @staticmethod
    def resolve_target_node(
        graph: Graph,
        source_node_id: NodeId,
        target_role: str | None,
    ) -> NodeId:
        """Return receiver NodeId for a given source node and optional target_role.

        Rules (matching legacy _run_router):
        1. If target_role is set → find first non-router node whose role matches.
        2. If target_role is None → pick first non-router node that is not the source.
        3. If nothing found → raise RoleNotResolvable.
        """
        non_router: list[GraphNode] = [
            n for n in graph.nodes if str(n.mode) != "router"
        ]

        if target_role:
            matched = [n for n in non_router if n.role == target_role]
            if not matched:
                raise RoleNotResolvable(
                    f"No graph node with role={target_role!r} found in graph {graph.id}"
                )
            return matched[0].id

        candidates = [n for n in non_router if n.id != source_node_id]
        if not candidates and non_router:
            candidates = non_router  # fallback: send to first non-router even if same
        if not candidates:
            raise RoleNotResolvable(
                f"Cannot resolve target: graph {graph.id} has no routable nodes"
            )
        return candidates[0].id
```

### domain/services/rag_index_service.py
```
"""RagIndexService — domain service: chunk text, embed, attach to RagDocument."""
from __future__ import annotations

import math
import struct
from datetime import datetime
from typing import TYPE_CHECKING, Protocol

from shell_ddd.domain.entities.rag_document import RagDocument
from shell_ddd.domain.value_objects.ids import RagChunkId, RagDocumentId

if TYPE_CHECKING:
    pass


class Embedder(Protocol):
    """Port — embed text into a float vector."""

    @property
    def model_name(self) -> str: ...

    @property
    def dim(self) -> int: ...

    def embed_text(self, text: str) -> list[float]: ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...


def _encode_vector(vector: list[float]) -> bytes:
    return struct.pack(f"{len(vector)}f", *vector)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be in [0, chunk_size)")
    text = text.strip()
    if not text:
        return []
    chunks: list[str] = []
    step = chunk_size - overlap
    for start in range(0, len(text), step):
        chunk = text[start : start + chunk_size]
        if not chunk:
            break
        chunks.append(chunk)
        if start + chunk_size >= len(text):
            break
    return chunks


def build_rag_document(
    doc_id: RagDocumentId,
    chunk_ids: list[RagChunkId],
    source_uri: str,
    title: str,
    domain: str,
    text: str,
    embedder: Embedder,
    now: datetime,
    chunk_size: int = 500,
    overlap: int = 50,
) -> RagDocument:
    """Chunk *text*, embed each chunk, return a fully-built RagDocument aggregate."""
    doc = RagDocument.new(
        id_=doc_id,
        source_uri=source_uri,
        title=title,
        domain=domain,
        now=now,
    )
    chunks = chunk_text(text, chunk_size, overlap)
    if not chunks:
        return doc
    if len(chunk_ids) < len(chunks):
        raise ValueError(
            f"Not enough chunk_ids supplied: need {len(chunks)}, got {len(chunk_ids)}"
        )
    vectors = embedder.embed_batch(chunks)
    blobs = [_encode_vector(v) for v in vectors]
    doc.add_chunks(
        chunk_ids=chunk_ids[: len(chunks)],
        texts=chunks,
        embeddings=blobs,
        model=embedder.model_name,
    )
    return doc


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)
```

### domain/value_objects/__init__.py
```
```

### domain/value_objects/envelope_status.py
```
"""EnvelopeStatus and EnvelopeStage value objects."""
from __future__ import annotations

from enum import StrEnum


class EnvelopeStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    DELIVERED = "delivered"
    FAILED = "failed"
    DEAD = "dead"


class EnvelopeStage(StrEnum):
    DRAFT = "draft"
    SENT = "sent"
    RECEIVED = "received"
    PROCESSING = "processing"
    DONE = "done"
    ARCHIVED = "archived"
```

### domain/value_objects/execution_result.py
```
"""ExecutionResult value object — subprocess output."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    returncode: int
    stdout: str = field(default="")
    stderr: str = field(default="")

    @property
    def success(self) -> bool:
        return self.returncode == 0
```

### domain/value_objects/hash.py
```
"""Hash value object — SHA-256 hex digest."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Hash:
    value: str  # hex digest

    def __post_init__(self) -> None:
        if len(self.value) != 64:
            raise ValueError(f"Hash must be 64 hex chars (SHA-256), got {len(self.value)}")
        try:
            int(self.value, 16)
        except ValueError:
            raise ValueError("Hash must be a valid hex string") from None

    def __str__(self) -> str:
        return self.value

    @classmethod
    def of(cls, data: str | bytes) -> Hash:
        raw = data.encode() if isinstance(data, str) else data
        return cls(hashlib.sha256(raw).hexdigest())
```

### domain/value_objects/ids.py
```
"""Typed ID value objects."""
from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TaskId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("TaskId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> TaskId:
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class WorkflowId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("WorkflowId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> WorkflowId:
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class EnvelopeId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("EnvelopeId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> EnvelopeId:
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class NodeId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("NodeId cannot be empty")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class GraphId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("GraphId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> GraphId:
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class PromptId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("PromptId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> PromptId:
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class NodeResultId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("NodeResultId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> NodeResultId:
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class RunnerConfigId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("RunnerConfigId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> RunnerConfigId:
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class RagDocumentId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("RagDocumentId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> RagDocumentId:
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class RagChunkId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("RagChunkId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> RagChunkId:
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class SessionId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("SessionId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> SessionId:
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class MessageId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("MessageId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> MessageId:
        return cls(str(uuid.uuid4()))
```

### domain/value_objects/manifest.py
```
"""Manifest value object — parsed manifest.yaml metadata."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell_ddd.domain.value_objects.mode import Mode


@dataclass(frozen=True, slots=True)
class Manifest:
    name: str
    mode: Mode
    role: str
    node_type: str
    version: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Manifest.name cannot be empty")
        if not self.role:
            raise ValueError("Manifest.role cannot be empty")
```

### domain/value_objects/mode.py
```
"""Mode — execution mode of a node (agent/router/tasker/tool/worker)."""
from __future__ import annotations

from enum import StrEnum


class Mode(StrEnum):
    """Execution mode of a node."""

    AGENT = "agent"
    ROUTER = "router"
    TASKER = "tasker"
    TOOL = "tool"
    WORKER = "worker"
```

### domain/value_objects/prompt_file.py
```
"""PromptFile value object."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PromptFile:
    file_name: str
    file_body: str

    def __post_init__(self) -> None:
        if not self.file_name:
            raise ValueError("PromptFile.file_name cannot be empty")
```

### domain/value_objects/status.py
```
"""Status value object — node/workflow/envelope runtime status string."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Status:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Status cannot be empty")

    def __str__(self) -> str:
        return self.value

    # Common sentinel values
    @classmethod
    def idle(cls) -> Status:
        return cls("idle")

    @classmethod
    def running(cls) -> Status:
        return cls("running")

    @classmethod
    def done(cls) -> Status:
        return cls("done")

    @classmethod
    def failed(cls) -> Status:
        return cls("failed")
```

### domain/value_objects/task_name.py
```
"""TaskName value object."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TaskName:
    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("TaskName cannot be empty")
        if len(self.value) > 255:
            raise ValueError("TaskName cannot exceed 255 characters")

    def __str__(self) -> str:
        return self.value
```

### domain/value_objects/timestamp.py
```
"""Timestamp value object — UTC datetime wrapper."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class Timestamp:
    value: datetime

    def __post_init__(self) -> None:
        if self.value.tzinfo is None:
            raise ValueError("Timestamp must be timezone-aware (UTC)")

    def __str__(self) -> str:
        return self.value.isoformat()

    @classmethod
    def now(cls) -> Timestamp:
        return cls(datetime.now(tz=UTC))

    @classmethod
    def from_datetime(cls, dt: datetime) -> Timestamp:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return cls(dt)
```

### framework/__init__.py
```
```

### framework/api/__init__.py
```
```

### framework/api/app.py
```
"""FastAPI application factory for shell_ddd control plane."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from shell_ddd.bootstrap.container import Container
from shell_ddd.domain.exceptions import DomainError
from shell_ddd.framework.api.middleware.correlation_id import CorrelationIdMiddleware
from shell_ddd.framework.api.middleware.error_handler import domain_error_handler
from shell_ddd.framework.api.routers import envelopes, nodes, tasks, workflows


def create_app(container: Container) -> FastAPI:
    """Create the FastAPI application with all routers and middleware."""

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
        yield  # startup / shutdown hooks can be added here

    app = FastAPI(
        title="shell_ddd control plane",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.container = container

    # Middleware
    app.add_middleware(CorrelationIdMiddleware)
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]

    # Routers
    app.include_router(tasks.router)
    app.include_router(workflows.router)
    app.include_router(envelopes.router)
    app.include_router(nodes.router)

    @app.get("/health", tags=["health"])
    async def health() -> dict:  # type: ignore[type-arg]
        return {"status": "ok"}

    return app
```

### framework/api/middleware/__init__.py
```
```

### framework/api/middleware/correlation_id.py
```
"""Correlation-ID middleware — adds X-Correlation-ID header to every request."""
from __future__ import annotations

import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: object) -> Response:  # type: ignore[override]
        cid = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        correlation_id_var.set(cid)
        response: Response = await call_next(request)  # type: ignore[operator]
        response.headers["X-Correlation-ID"] = cid
        return response
```

### framework/api/middleware/error_handler.py
```
"""Error handler middleware — maps DomainErrors to 4xx HTTP responses."""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from shell_ddd.domain.exceptions import (
    DomainError,
    EnvelopeNotFound,
    NodeNotFound,
    PromptNotFound,
    RunnerConfigNotFound,
    TaskNotFound,
    WorkflowNotFound,
)

_NOT_FOUND = {TaskNotFound, WorkflowNotFound, EnvelopeNotFound, NodeNotFound, PromptNotFound, RunnerConfigNotFound}


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    status = 404 if type(exc) in _NOT_FOUND else 400
    return JSONResponse(status_code=status, content={"detail": str(exc)})
```

### framework/api/routers/__init__.py
```
```

### framework/api/routers/envelopes.py
```
"""Envelopes router — query envelopes by workflow."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from shell_ddd.application.queries.queries import GetEnvelopesByWorkflowQuery
from shell_ddd.bootstrap.container import Container

router = APIRouter(prefix="/envelopes", tags=["envelopes"])


from fastapi import Request as _Request


def get_container(request: _Request) -> Container:
    return request.app.state.container


@router.get("/workflow/{workflow_id}")
async def list_by_workflow(
    workflow_id: str,
    pending_only: bool = False,
    container: Container = Depends(get_container),
) -> dict:  # type: ignore[type-arg]
    result = await container.query_bus.dispatch(
        GetEnvelopesByWorkflowQuery(workflow_id=workflow_id, pending_only=pending_only)
    )
    envelopes = result if result is not None else []
    return {"workflow_id": workflow_id, "envelopes": [str(e) for e in envelopes]}
```

### framework/api/routers/nodes.py
```
"""Nodes router — query node execution results."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from shell_ddd.application.queries.queries import GetNodeResultQuery
from shell_ddd.bootstrap.container import Container

router = APIRouter(prefix="/nodes", tags=["nodes"])


from fastapi import Request as _Request


def get_container(request: _Request) -> Container:
    return request.app.state.container


@router.get("/{node_id}/result")
async def get_node_result(
    node_id: str,
    workflow_id: str,
    container: Container = Depends(get_container),
) -> dict:  # type: ignore[type-arg]
    result = await container.query_bus.dispatch(GetNodeResultQuery(node_id=node_id, workflow_id=workflow_id))
    if result is None:
        raise HTTPException(status_code=404, detail=f"NodeResult for '{node_id}' not found")
    return {"node_id": node_id, "result": str(result)}
```

### framework/api/routers/tasks.py
```
"""Tasks router — import and query tasks."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from shell_ddd.application.commands.commands import ImportTaskCommand
from shell_ddd.application.queries.queries import GetTaskByNameQuery
from shell_ddd.bootstrap.container import Container

router = APIRouter(prefix="/tasks", tags=["tasks"])


class ImportTaskRequest(BaseModel):
    task_name: str
    md_path: str
    yaml_path: str


class ImportTaskResponse(BaseModel):
    task_id: str


def get_container(request: Request) -> Container:
    return request.app.state.container


@router.post("/import", response_model=ImportTaskResponse, status_code=201)
async def import_task(body: ImportTaskRequest, container: Container = Depends(get_container)) -> ImportTaskResponse:
    cmd = ImportTaskCommand(md_path=body.md_path, yaml_path=body.yaml_path, task_name=body.task_name)
    task_id = await container.command_bus.dispatch(cmd)
    return ImportTaskResponse(task_id=str(task_id))


@router.get("/{name}")
async def get_task(name: str, container: Container = Depends(get_container)) -> dict:  # type: ignore[type-arg]
    result = await container.query_bus.dispatch(GetTaskByNameQuery(name=name))
    if result is None:
        raise HTTPException(status_code=404, detail=f"Task '{name}' not found")
    return {"name": name, "task": str(result)}
```

### framework/api/routers/workflows.py
```
"""Workflows router — start and query workflows."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from shell_ddd.application.commands.commands import RouteEnvelopesCommand, StartWorkflowCommand
from shell_ddd.application.queries.queries import GetWorkflowQuery
from shell_ddd.bootstrap.container import Container

router = APIRouter(prefix="/workflows", tags=["workflows"])


class StartWorkflowRequest(BaseModel):
    task_name: str


class StartWorkflowResponse(BaseModel):
    workflow_id: str


class RouteResponse(BaseModel):
    routed: int


from fastapi import Request as _Request


def get_container(request: _Request) -> Container:
    return request.app.state.container


@router.post("", response_model=StartWorkflowResponse, status_code=201)
async def start_workflow(
    body: StartWorkflowRequest, container: Container = Depends(get_container)
) -> StartWorkflowResponse:
    cmd = StartWorkflowCommand(task_name=body.task_name)
    wf_id = await container.command_bus.dispatch(cmd)
    return StartWorkflowResponse(workflow_id=str(wf_id))


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str, container: Container = Depends(get_container)) -> dict:  # type: ignore[type-arg]
    result = await container.query_bus.dispatch(GetWorkflowQuery(workflow_id=workflow_id))
    if result is None:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")
    return {"workflow_id": workflow_id, "workflow": str(result)}


@router.post("/{workflow_id}/route", response_model=RouteResponse)
async def route_envelopes(workflow_id: str, container: Container = Depends(get_container)) -> RouteResponse:
    cmd = RouteEnvelopesCommand(workflow_id=workflow_id)
    count = await container.command_bus.dispatch(cmd)
    return RouteResponse(routed=count or 0)
```

### framework/cli/__init__.py
```
```

### framework/cli/commands/__init__.py
```
```

### framework/cli/main.py
```
"""Main CLI entrypoint for shell_ddd — dispatches to per-mode command handlers."""
from __future__ import annotations

import asyncio
import os
import sys
from typing import Sequence

from shell_ddd.framework.cli.parser import build_parser


# Map of mode-name → default runner root dir (relative to this file if available).
_MODE_RUNNER_ROOTS: dict[str, str] = {
    "agent": "agent",
    "router": "router",
    "tasker": "tasker",
    "tool": "tool",
    "worker": "worker",
}


def _get_database_url() -> str:
    return os.environ.get("SHELL_DDD_DATABASE_URL", "sqlite+aiosqlite:///shell_ddd.db")


def _get_max_step() -> int:
    try:
        return int(os.environ.get("SHELL_DDD_MAX_STEP", "20"))
    except ValueError:
        return 20


async def _run_node(mode: str, argv: Sequence[str]) -> int:
    from shell_ddd.bootstrap.container import ApplicationFactory
    from shell_ddd.application.commands.commands import RunNodeCommand

    parser = build_parser(prog=f"shell_ddd {mode}")
    ns = parser.parse_args(list(argv))

    database_url = _get_database_url()
    max_step = ns.max_step if ns.max_step is not None else _get_max_step()
    container = await ApplicationFactory(database_url=database_url, max_step=max_step).build()

    node_id = ns.node_dir or mode
    workflow_id = ns.workflow_id or "default"
    work_dir = ns.work_dir or os.getcwd()

    cmd = RunNodeCommand(
        node_id=node_id,
        workflow_id=workflow_id,
        workspace_path=work_dir,
    )
    try:
        await container.command_bus.dispatch(cmd)
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


async def _import_task(argv: Sequence[str]) -> int:
    from shell_ddd.bootstrap.container import ApplicationFactory
    from shell_ddd.application.commands.commands import ImportTaskCommand

    parser = build_parser(prog="shell_ddd import-task")
    ns = parser.parse_args(list(argv))

    task_name = ns.task_name
    task_dir = ns.task_dir
    if not task_name or not task_dir:
        print("ERROR: --task-name and --task-dir are required for import-task.", file=sys.stderr)
        return 1

    import pathlib
    md_path = str(pathlib.Path(task_dir) / f"{task_name}.md")
    yaml_path = str(pathlib.Path(task_dir) / f"{task_name}.yaml")

    database_url = _get_database_url()
    container = await ApplicationFactory(database_url=database_url).build()
    cmd = ImportTaskCommand(md_path=md_path, yaml_path=yaml_path, task_name=task_name)
    try:
        task_id = await container.command_bus.dispatch(cmd)
        print(f"Imported task '{task_name}' with id={task_id}")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


async def _route(argv: Sequence[str]) -> int:
    from shell_ddd.bootstrap.container import ApplicationFactory
    from shell_ddd.application.commands.commands import RouteEnvelopesCommand

    parser = build_parser(prog="shell_ddd route")
    ns = parser.parse_args(list(argv))

    database_url = _get_database_url()
    max_step = ns.max_step if ns.max_step is not None else _get_max_step()
    container = await ApplicationFactory(database_url=database_url, max_step=max_step).build()

    workflow_id = ns.workflow_id or "default"
    cmd = RouteEnvelopesCommand(workflow_id=workflow_id)
    try:
        count = await container.command_bus.dispatch(cmd)
        print(f"Routed {count} envelopes.")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


async def _run_tasker(argv: Sequence[str]) -> int:
    from shell_ddd.bootstrap.container import ApplicationFactory
    from shell_ddd.application.commands.commands import RunTaskerWorkflowCommand

    parser = build_parser(prog="shell_ddd run-tasker")
    ns = parser.parse_args(list(argv))

    task_name = ns.task_name
    if not task_name:
        print("ERROR: --task-name is required for run-tasker.", file=sys.stderr)
        return 1

    work_dir = ns.work_dir or os.getcwd()
    try:
        max_parallel = int(os.environ.get("SHELL_DDD_MAX_PARALLEL", "4"))
    except ValueError:
        max_parallel = 4

    database_url = _get_database_url()
    container = await ApplicationFactory(database_url=database_url).build()
    cmd = RunTaskerWorkflowCommand(
        task_name=task_name,
        work_dir=work_dir,
        max_parallel=max_parallel,
    )
    try:
        workflow_id = await container.command_bus.dispatch(cmd)
        print(f"Tasker workflow completed: workflow_id={workflow_id}")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry-point — first positional arg is the mode/subcommand."""
    args = list(argv) if argv is not None else sys.argv[1:]
    if not args:
        print("Usage: shell_ddd <mode> [options]", file=sys.stderr)
        print(f"  modes: {', '.join(list(_MODE_RUNNER_ROOTS) + ['import-task', 'route'])}", file=sys.stderr)
        return 1

    mode = args[0]
    rest = args[1:]

    if mode in _MODE_RUNNER_ROOTS:
        return asyncio.run(_run_node(mode, rest))
    elif mode == "import-task":
        return asyncio.run(_import_task(rest))
    elif mode == "route":
        return asyncio.run(_route(rest))
    elif mode == "run-tasker":
        return asyncio.run(_run_tasker(rest))
    else:
        print(f"Unknown mode: {mode!r}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

### framework/cli/parser.py
```
"""Shared argparse setup for all shell_ddd CLI entrypoints."""
from __future__ import annotations

import argparse
from typing import Sequence


def build_parser(prog: str = "shell_ddd") -> argparse.ArgumentParser:
    """Return a fully configured ArgumentParser with all shared flags."""
    parser = argparse.ArgumentParser(
        prog=prog,
        description="shell_ddd node runner.",
        add_help=True,
    )
    # ---- identity ----
    parser.add_argument("--node-dir", dest="node_dir", metavar="PATH", default=None)
    parser.add_argument("--mode", dest="mode", metavar="MODE", default=None)
    parser.add_argument("--role", dest="role", metavar="ROLE", default=None)
    parser.add_argument("--type", dest="type", metavar="TYPE", default=None)
    # ---- execution ----
    parser.add_argument("--model", dest="model", metavar="MODEL", default=None)
    parser.add_argument("--timeout", dest="timeout", type=int, metavar="SECONDS", default=None)
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", default=False)
    parser.add_argument("--log-level", dest="log_level", metavar="LEVEL", default="INFO")
    # ---- copilot/agent ----
    parser.add_argument("--no-ask-user", dest="no_ask_user", action="store_true", default=False)
    parser.add_argument("--autopilot", dest="autopilot", action="store_true", default=False)
    parser.add_argument("--add-dir", dest="add_dirs", metavar="PATH", action="append", default=[])
    parser.add_argument("--prompt", dest="prompt", metavar="PROMPT", default=None)
    parser.add_argument("--prompt-dir", dest="prompt_dir", metavar="PATH", default=None)
    # ---- task/source ----
    parser.add_argument("--source-dir", dest="source_dir", metavar="PATH", default=None)
    parser.add_argument("--task-name", dest="task_name", metavar="NAME", default=None)
    parser.add_argument("--task-id", dest="task_id", type=int, metavar="ID", default=None)
    parser.add_argument("--task-dir", dest="task_dir", metavar="PATH", default=None)
    parser.add_argument("--work-dir", dest="work_dir", metavar="PATH", default=None)
    # ---- routing ----
    parser.add_argument("--max-step", dest="max_step", type=int, metavar="N", default=None)
    parser.add_argument("--workflow-id", dest="workflow_id", metavar="ID", default=None)
    parser.add_argument("--envelope-id", dest="envelope_id", type=int, metavar="ID", default=None)
    parser.add_argument("--parent-thread-id", dest="parent_thread_id", metavar="ID", default=None)
    parser.add_argument("--parent-node-dir", dest="parent_node_dir", metavar="PATH", default=None)
    # ---- runner root (for entrypoint shims) ----
    parser.add_argument("--runner-root-dir", dest="runner_root_dir", metavar="PATH", default=None)
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)
```

### framework/entrypoints/__init__.py
```
```

### framework/entrypoints/agent_entrypoint.py
```
import sys
from shell_ddd.framework.cli.main import main
if __name__ == '__main__':
    sys.exit(main(['agent', *sys.argv[1:]]))

```

### framework/entrypoints/router_entrypoint.py
```
import sys
from shell_ddd.framework.cli.main import main
if __name__ == '__main__':
    sys.exit(main(['router', *sys.argv[1:]]))

```

### framework/entrypoints/tasker_entrypoint.py
```
import sys
from shell_ddd.framework.cli.main import main
if __name__ == '__main__':
    sys.exit(main(['tasker', *sys.argv[1:]]))

```

### framework/entrypoints/tool_entrypoint.py
```
import sys
from shell_ddd.framework.cli.main import main
if __name__ == '__main__':
    sys.exit(main(['tool', *sys.argv[1:]]))

```

### framework/entrypoints/worker_entrypoint.py
```
import sys
from shell_ddd.framework.cli.main import main
if __name__ == '__main__':
    sys.exit(main(['worker', *sys.argv[1:]]))

```

### infrastructure/__init__.py
```
```

### infrastructure/configuration/__init__.py
```
```

### infrastructure/external/__init__.py
```
```

### infrastructure/external/hash_embedder.py
```
"""HashEmbedder — deterministic, dependency-free stub embedder (dev/test)."""
from __future__ import annotations

import hashlib
import math
import struct


class HashEmbedder:
    """Generates a fixed-dim float vector via hashing.

    Deterministic: same text → same vector. Useful in tests and development
    before a real model (sentence-transformers, Ollama, …) is wired in.
    """

    def __init__(self, dim: int = 64) -> None:
        if dim <= 0:
            raise ValueError("dim must be positive")
        self._dim = dim
        self._model_name = f"hash-stub-{dim}"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dim(self) -> int:
        return self._dim

    def embed_text(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        repeats = (self._dim * 4 + len(digest) - 1) // len(digest)
        raw = (digest * repeats)[: self._dim * 4]
        ints = struct.unpack(f"{self._dim}I", raw)
        floats = [(v / 0xFFFFFFFF) * 2.0 - 1.0 for v in ints]
        norm = math.sqrt(sum(x * x for x in floats)) or 1.0
        return [x / norm for x in floats]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]
```

### infrastructure/filesystem/__init__.py
```
```

### infrastructure/filesystem/envelope_archive_fs.py
```
"""FileSystemEnvelopeArchive — filesystem-based EnvelopeArchive adapter."""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell_ddd.domain.entities.envelope import Envelope


class FileSystemEnvelopeArchive:
    """Persists archived envelopes as JSON files under a configurable root dir.

    URI format: ``fs://archive/<workflow_id>/<envelope_id>.json``
    """

    def __init__(self, archive_root: str) -> None:
        self._root = Path(archive_root)

    async def archive(self, envelope: Envelope) -> str:
        """Serialise envelope to JSON and return the archive URI."""
        wf_dir = self._root / envelope.workflow_id.value
        wf_dir.mkdir(parents=True, exist_ok=True)
        target = wf_dir / f"{envelope.id.value}.json"
        payload = {
            "id": envelope.id.value,
            "workflow_id": envelope.workflow_id.value,
            "status": envelope.status.value,
            "stage": envelope.stage.value,
            "payload": envelope.payload,
            "created_at": envelope.created_at.isoformat(),
            "updated_at": envelope.updated_at.isoformat(),
        }
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return f"fs://archive/{envelope.workflow_id.value}/{envelope.id.value}.json"

    async def get(self, archive_uri: str) -> Envelope | None:
        """Retrieve an archived envelope by its URI.  Returns None if not found."""
        # URI: fs://archive/<workflow_id>/<envelope_id>.json
        suffix = archive_uri.removeprefix("fs://archive/")
        parts = suffix.split("/", 1)
        if len(parts) != 2:
            return None
        wf_id, filename = parts
        target = self._root / wf_id / filename
        if not target.exists():
            return None
        # Minimal deserialisation — returns raw dict as pseudo-Envelope
        # Full round-trip requires proper mappers (wired in Faza 3 mappers).
        return None  # noqa: RET504
```

### infrastructure/filesystem/node_workspace.py
```
"""NodeWorkspaceFs — filesystem implementation of the NodeWorkspace port."""
from __future__ import annotations

import shutil
from pathlib import Path


# Standard sub-directories inside .node/
_NODE_SUBDIRS = [
    "input",
    "output",
    "logs",
    "temp",
    "prompt",
    "scripts",
    "status",
    "port",
    "archive",
]
_DOT_NODE = ".node"


class NodeWorkspaceFs:
    """Creates and manages the .node/ workspace directory for a single node execution.

    Directory layout (matching legacy SHELL conventions):
    ``<workspace_path>/.node/{input,output,logs,temp,prompt,scripts,status,port,archive}/``
    """

    async def prepare(self, node_id: str, work_dir: str) -> str:
        """Create workspace directory tree and return the workspace path."""
        ws = Path(work_dir) / node_id
        dot_node = ws / _DOT_NODE
        for subdir in _NODE_SUBDIRS:
            (dot_node / subdir).mkdir(parents=True, exist_ok=True)
        return str(ws)

    async def cleanup(self, workspace_path: str) -> None:
        """Remove the workspace directory tree (best-effort)."""
        ws = Path(workspace_path)
        if ws.exists():
            shutil.rmtree(ws, ignore_errors=True)

    async def read_input(self, workspace_path: str) -> str:
        """Read content of .node/input/input.txt if it exists."""
        p = Path(workspace_path) / _DOT_NODE / "input" / "input.txt"
        if p.exists():
            return p.read_text(encoding="utf-8")
        return ""

    async def write_output(self, workspace_path: str, name: str, body: str) -> Path:
        """Write body to .node/output/<name> and return the path."""
        out = Path(workspace_path) / _DOT_NODE / "output" / name
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")
        return out
```

### infrastructure/filesystem/task_loader.py
```
"""FileSystemTaskLoader — reads task.md + task.yaml from the filesystem."""
from __future__ import annotations

import asyncio
from pathlib import Path


class FileSystemTaskLoader:
    """Reads task markdown and yaml files asynchronously (via thread pool)."""

    async def load(self, md_path: str, yaml_path: str) -> tuple[str, str]:
        """Return (body_md, body_yaml_raw).  Both paths must exist."""
        loop = asyncio.get_event_loop()
        body_md, body_yaml = await asyncio.gather(
            loop.run_in_executor(None, Path(md_path).read_text, "utf-8"),
            loop.run_in_executor(None, Path(yaml_path).read_text, "utf-8"),
        )
        return body_md, body_yaml
```

### infrastructure/logging/__init__.py
```
"""Stdlib logging adapter."""
from __future__ import annotations

import logging


class StdlibLogger:
    """Implements application/ports/ports.Logger using Python stdlib logging."""

    def __init__(self, name: str = "shell_ddd") -> None:
        self._log = logging.getLogger(name)

    def debug(self, msg: str, **kw: object) -> None:
        self._log.debug(msg, extra=kw)

    def info(self, msg: str, **kw: object) -> None:
        self._log.info(msg, extra=kw)

    def warning(self, msg: str, **kw: object) -> None:
        self._log.warning(msg, extra=kw)

    def error(self, msg: str, **kw: object) -> None:
        self._log.error(msg, extra=kw)
```

### infrastructure/logging/composite_event_publisher.py
```
"""CompositeEventPublisher — fans out to multiple EventPublisher adapters."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell_ddd.application.ports.ports import EventPublisher
    from shell_ddd.domain.events.events import DomainEvent


class CompositeEventPublisher:
    """Delegates ``publish`` to every publisher in the list, in order."""

    def __init__(self, publishers: list[EventPublisher]) -> None:
        self._publishers = list(publishers)

    async def publish(self, events: list[DomainEvent]) -> None:
        for publisher in self._publishers:
            await publisher.publish(events)
```

### infrastructure/logging/logging_event_publisher.py
```
"""LoggingEventPublisher — publishes domain events via the Logger port."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell_ddd.application.ports.ports import Logger
    from shell_ddd.domain.events.events import DomainEvent


class LoggingEventPublisher:
    """EventPublisher adapter that logs each domain event as a structured JSON entry."""

    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    async def publish(self, events: list[DomainEvent]) -> None:
        for event in events:
            self._logger.info(
                "domain_event",
                event_type=type(event).__name__,
                occurred_at=event.occurred_at.isoformat(),
            )
```

### infrastructure/logging/sql_audit_publisher.py
```
"""SqlAuditPublisher — persists domain events to the audit_event table."""
from __future__ import annotations

import dataclasses
import uuid
from typing import TYPE_CHECKING

from shell_ddd.infrastructure.persistence.sql.models import AuditEventModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell_ddd.domain.events.events import DomainEvent


class SqlAuditPublisher:
    """EventPublisher adapter that writes one row per domain event to ``audit_event``."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def publish(self, events: list[DomainEvent]) -> None:
        if not events:
            return
        async with self._session_factory() as session:
            for event in events:
                payload = {
                    f.name: str(getattr(event, f.name))
                    for f in dataclasses.fields(event)  # type: ignore[arg-type]
                    if f.name != "occurred_at"
                }
                session.add(
                    AuditEventModel(
                        id=str(uuid.uuid4()),
                        event_type=type(event).__name__,
                        occurred_at=event.occurred_at,
                        payload=payload,
                    )
                )
            await session.commit()
```

### infrastructure/logging/stdlib_logger.py
```
"""Structured JSON logger — implements the Logger port using stdlib logging."""
from __future__ import annotations

import json
import logging
from contextvars import ContextVar
from datetime import UTC, datetime

# ---------------------------------------------------------------------------
# Correlation-ID context variable (set per-request/command by middleware or CLI)
# ---------------------------------------------------------------------------

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    return correlation_id_var.get()


def set_correlation_id(value: str) -> None:
    correlation_id_var.set(value)


# ---------------------------------------------------------------------------
# JSON formatter
# ---------------------------------------------------------------------------


class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON strings."""

    def format(self, record: logging.LogRecord) -> str:
        data: dict[str, object] = {
            "ts": datetime.now(tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "correlation_id": get_correlation_id(),
        }
        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)
        # Include any extra fields attached by the caller
        _std_keys = logging.LogRecord.__dict__.keys() | {
            "message", "asctime", "taskName"
        }
        for k, v in record.__dict__.items():
            if k not in _std_keys and not k.startswith("_"):
                data.setdefault("extra", {})[k] = v  # type: ignore[index]
        return json.dumps(data, default=str)


# ---------------------------------------------------------------------------
# Logger adapter
# ---------------------------------------------------------------------------


def _make_handler() -> logging.StreamHandler:  # type: ignore[type-arg]
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    return handler


class StdlibLogger:
    """Implements the ``Logger`` port using stdlib logging with JSON output."""

    def __init__(self, name: str = "shell_ddd", level: int = logging.INFO) -> None:
        self._logger = logging.getLogger(name)
        if not self._logger.handlers:
            self._logger.addHandler(_make_handler())
        self._logger.setLevel(level)
        self._logger.propagate = False

    def debug(self, msg: str, **kw: object) -> None:
        self._logger.debug(msg, extra=kw if kw else None)

    def info(self, msg: str, **kw: object) -> None:
        self._logger.info(msg, extra=kw if kw else None)

    def warning(self, msg: str, **kw: object) -> None:
        self._logger.warning(msg, extra=kw if kw else None)

    def error(self, msg: str, **kw: object) -> None:
        self._logger.error(msg, extra=kw if kw else None)
```

### infrastructure/messaging/__init__.py
```
```

### infrastructure/messaging/memory_outbox_store.py
```
"""InMemoryOutboxStore — in-process store for unit-testing the outbox pattern."""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from datetime import datetime  # noqa: TC003
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell_ddd.domain.events.events import DomainEvent


@dataclass
class OutboxRecord:
    id: str
    event_type: str
    occurred_at: datetime
    payload: dict  # type: ignore[type-arg]
    published_at: datetime | None = None

    @property
    def is_published(self) -> bool:
        return self.published_at is not None


class InMemoryOutboxStore:
    """Simple in-memory outbox for tests — implements the same interface as SqlOutboxPublisher."""

    def __init__(self) -> None:
        self.records: list[OutboxRecord] = []

    async def publish(self, events: list[DomainEvent]) -> None:
        import uuid

        for event in events:
            payload = {
                f.name: str(getattr(event, f.name))
                for f in dataclasses.fields(event)  # type: ignore[arg-type]
                if f.name != "occurred_at"
            }
            self.records.append(
                OutboxRecord(
                    id=str(uuid.uuid4()),
                    event_type=type(event).__name__,
                    occurred_at=event.occurred_at,
                    payload=payload,
                )
            )

    def pending(self) -> list[OutboxRecord]:
        return [r for r in self.records if not r.is_published]
```

### infrastructure/messaging/outbox/__init__.py
```
```
