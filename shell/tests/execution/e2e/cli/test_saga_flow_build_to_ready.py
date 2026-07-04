"""E2E test: build graph via saga → create nodes → link → ready."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.application.execution.command_handlers.node_execution_create_handler import (
    NodeExecutionCreateHandler,
)
from shell.application.execution.commands.create_node_execution_command import (
    CreateNodeExecutionCommand,
)
from shell.application.execution.event_handlers.build_graph_execution_on_task_execution_created_event_handler import (
    BuildGraphExecutionOnTaskExecutionCreatedEventHandler,
)
from shell.domain.definition.aggregates.graph_definition.graph_definition import GraphDefinition
from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
    GraphDefinitionId,
)
from shell.domain.definition.aggregates.node_definition.node_definition import (
    NodeDefinition,
)
from shell.domain.definition.aggregates.node_definition.value_objects.node_definition_id import (
    NodeDefinitionId,
)
from shell.domain.definition.aggregates.node_link_definition.node_link_definition import (
    NodeLinkDefinition,
)
from shell.domain.definition.aggregates.node_link_definition.value_objects.node_link_definition_id import (
    NodeLinkDefinitionId,
)
from shell.domain.definition.value_objects.graph_name import GraphName
from shell.domain.execution.aggregates.graph_execution.events.graph_execution_initialized_event import (
    GraphExecutionInitializedEvent,
)
from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.events import TaskExecutionCreatedEvent
from shell.domain.execution.value_objects.graph_execution_definition import (
    GraphExecutionDefinition,
    NodeExecutionDefinition,
)
from shell.domain.execution.value_objects.ids import TaskExecutionId
from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.mode import Mode
from shell.infrastructure.definition.persistence.memory.in_memory_node_link_definition_repository import (
    InMemoryNodeLinkDefinitionRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_node_execution_repository import (
    InMemoryNodeExecutionRepository,
)
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,
    FakeIdGenerator,
    FakeLogger,
    InMemoryGraphDefinitionRepository,
    InMemoryGraphExecutionRepository,
    InMemoryNodeDefinitionRepository,
    InMemoryUnitOfWork,
)
from shell.process.execution.graph_execution_saga.graph_execution_saga import (
    GraphExecutionSaga,
)
from shell.process.execution.graph_execution_saga.handlers.graph_execution_initialized_handler import (
    GraphExecutionInitializedHandler,
)
from shell.process.execution.graph_execution_saga.handlers.node_execution_initialized_handler import (
    NodeExecutionInitializedHandler,
)
from shell.process.execution.graph_execution_saga.state import (
    GraphExecutionSagaStatus,
)
from shell.tests.process.conftest import (
    FakeCommandOutboxPublisher,
    InMemoryGraphExecutionSagaRepository,
)
from shell.tests.process.conftest import (
    FakeLogger as ProcessFakeLogger,
)

from shell.infrastructure.execution.persistence.memory.in_memory_node_link_execution_repository import (
            InMemoryNodeLinkExecutionRepository,
        )
NOW = datetime.now(tz=UTC)


class _InMemoryDefinitionProvider:
    def __init__(self, unit_of_work: InMemoryUnitOfWork) -> None:
        self._repo = unit_of_work.repository(InMemoryGraphDefinitionRepository)
        self._node_repo = unit_of_work.repository(InMemoryNodeDefinitionRepository)
        self._link_repo = unit_of_work.repository(InMemoryNodeLinkDefinitionRepository)

    async def get_graph_definition_by_semantic_name(
        self,
        query: object,
    ) -> GraphExecutionDefinition | None:
        role = getattr(query, "default_graph_definition", None)
        if role is not None:
            for def_entity in await self._repo.list_all():
                if def_entity.system_role is not None and def_entity.system_role.value == role:
                    return await self._to_dto(def_entity)
        entity = await self._repo.get_graph_definition_by_name(
            GraphName(getattr(query, "text", str(query))),
        )
        if entity is None:
            return None
        return await self._to_dto(entity)

    async def get_graph_definition(self, definition_id: str) -> GraphExecutionDefinition | None:
        entity = await self._repo.get_by_id(GraphDefinitionId(definition_id))
        if entity is None:
            return None
        return await self._to_dto(entity)

    async def _to_dto(self, entity: object) -> GraphExecutionDefinition:
        graph_definition: GraphDefinition = entity
        links = await self._link_repo.list_by_graph_definition_id(graph_definition.id)
        nodes: list[NodeDefinition] = []
        for link in links:
            node = await self._node_repo.get_by_id(link.node_definition_id)
            if node is not None:
                nodes.append(node)
        return GraphExecutionDefinition(
            id=graph_definition.id.value,
            name=graph_definition.name.value,
            node_execution_definitions=[
                NodeExecutionDefinition(
                    position=node.position.value,
                    mode=node.mode.value,
                    role=node.role.value,
                    node_type=node.node_type.value,
                    model=node.model.value if node.model else "",
                    command=node.command.value if node.command else "",
                    timeout=node.timeout.value if node.timeout else 0,
                    retries=node.retries.value if node.retries else 0,
                    log_level=node.log_level.value if node.log_level else "INFO",
                    max_step=node.max_step.value if node.max_step else None,
                    no_ask_user=node.no_ask_user.value if node.no_ask_user else False,
                    autopilot=node.autopilot.value if node.autopilot else False,
                    status_initial=node.status_initial.value if node.status_initial else "",
                    script=node.script.value if node.script else "",
                    script_type=node.script_type.value if node.script_type else "",
                )
                for node in nodes
            ],
        )


async def _seed_graph_definition(
    unit_of_work: InMemoryUnitOfWork, name: str = "base_planner"
) -> GraphDefinition:
    now = datetime.now(UTC)
    node1_id = NodeDefinitionId("ndef-1")
    node2_id = NodeDefinitionId("ndef-2")

    node1 = NodeDefinition.create(
        id=node1_id,
        position=NodePosition(0),
        mode=Mode("agent"),
        role=NodeRoleName("PLANNER"),
        node_type=NodeTypeName("planner"),
        now=now,
    )
    node2 = NodeDefinition.create(
        id=node2_id,
        position=NodePosition(1),
        mode=Mode("agent"),
        role=NodeRoleName("AGENT"),
        node_type=NodeTypeName("agent"),
        now=now,
    )
    await unit_of_work.repository(InMemoryNodeDefinitionRepository).save(node1)
    await unit_of_work.repository(InMemoryNodeDefinitionRepository).save(node2)

    repo = unit_of_work.repository(InMemoryGraphDefinitionRepository)
    keys_to_remove = [k for k, v in repo._store.items() if v.name.value == name]
    for k in keys_to_remove:
        del repo._store[k]

    graph_definition = GraphDefinition.create(
        id=GraphDefinitionId(f"{name}-id"),
        name=GraphName(name),
        purpose=Purpose("planning"),
        system_role=SystemRole.PLANNER,
        now=now,
    )
    await repo.save(graph_definition)

    link_repo = unit_of_work.repository(InMemoryNodeLinkDefinitionRepository)
    await link_repo.save(
        NodeLinkDefinition(
            id=NodeLinkDefinitionId.generate(),
            graph_definition_id=graph_definition.id,
            node_definition_id=node1_id,
        )
    )
    await link_repo.save(
        NodeLinkDefinition(
            id=NodeLinkDefinitionId.generate(),
            graph_definition_id=graph_definition.id,
            node_definition_id=node2_id,
        )
    )
    return graph_definition


class TestSagaFlowBuildToReady:
    async def test_full_flow_with_two_nodes(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        fake_logger: FakeLogger,
    ) -> None:
        # ── 1. Seed graph definition ──
        await _seed_graph_definition(unit_of_work)
        definition_provider = _InMemoryDefinitionProvider(unit_of_work)

        # ── 2. Build graph execution ──
        build_handler = BuildGraphExecutionOnTaskExecutionCreatedEventHandler(
            unit_of_work=unit_of_work,
            definition_provider=definition_provider,
            clock=clock,
            id_generator=id_generator,
            logger=fake_logger,
        )
        task_event = TaskExecutionCreatedEvent.now(
            task_execution_id=TaskExecutionId("task-e2e"),
            task_execution_name=TaskExecutionName("e2e-test"),
            now=CreatedAt.from_datetime(clock.now()),
        )

        async with unit_of_work:
            await build_handler.handle(task_event)

        graph_execution = await unit_of_work.repository(
            InMemoryGraphExecutionRepository
        ).get_by_task_execution_id(TaskExecutionId("task-e2e"))
        assert graph_execution is not None

        # Verify GraphExecutionInitializedEvent was emitted
        initialized_events = [
            e
            for e in unit_of_work.committed_events
            if isinstance(e, GraphExecutionInitializedEvent)
        ]
        assert len(initialized_events) == 1
        initialized_event = initialized_events[0]
        graph_execution_id_str = initialized_event.graph_execution_id.value

        # ── 3. Saga: create saga → fetch linked node defs → publish CreateNodeExecutionCommand ──
        saga_repo = InMemoryGraphExecutionSagaRepository()
        saga = GraphExecutionSaga(repository=saga_repo)
        publisher = FakeCommandOutboxPublisher()
        process_logger = ProcessFakeLogger()

        link_def_repo = unit_of_work.repository(InMemoryNodeLinkDefinitionRepository)
        node_def_repo = unit_of_work.repository(InMemoryNodeDefinitionRepository)

        saga_handler = GraphExecutionInitializedHandler(
            saga_manager=saga,
            command_publisher=publisher,
            logger=process_logger,
            link_definition_repository=link_def_repo,
            node_definition_repository=node_def_repo,
        )
        await saga_handler.handle(initialized_event)

        created_cmds = [
            (cmd_type, payload)
            for cmd_type, payload in publisher.published
            if cmd_type == "CreateNodeExecutionCommand"
        ]
        assert len(created_cmds) == 2

        stored_saga = await saga_repo.get_by_graph_execution_id(graph_execution_id_str)
        assert stored_saga is not None
        assert stored_saga.expected_nodes_count == 2
        assert stored_saga.status == GraphExecutionSagaStatus.PENDING

        # ── 4. Process each CreateNodeExecutionCommand through handler ──
        identity_service = id_generator
        node_initialized_events: list = []

        create_handler = NodeExecutionCreateHandler(
            unit_of_work=unit_of_work,
            identity=identity_service,
            time=clock,
        )

        for _cmd_type, payload in created_cmds:
            cmd = CreateNodeExecutionCommand(
                graph_execution_id=payload["graph_execution_id"],
                node_definition_id=payload["node_definition_id"],
                position=payload["position"],
                role=payload["role"],
                mode=payload["mode"],
                node_type=payload["node_type"],
            )
            async with unit_of_work:
                await create_handler.handle(cmd)
                node_initialized_events.extend(
                    [
                        e
                        for e in unit_of_work.committed_events
                        if e.__class__.__name__ == "NodeExecutionInitializedEvent"
                    ]
                )

        # Verify nodes were created
        all_nodes = list(
            unit_of_work.repository(InMemoryNodeExecutionRepository)._store.values()
        )
        assert len(all_nodes) == 2
        assert len(node_initialized_events) == 2

        # ── 5. Saga node handler: create link for each node ──
        link_exec_repo = unit_of_work.repository(InMemoryNodeLinkExecutionRepository)

        node_event_publisher = FakeCommandOutboxPublisher()
        attach_handler_saga = NodeExecutionInitializedHandler(
            saga_manager=saga,
            command_publisher=node_event_publisher,
            link_execution_repository=link_exec_repo,
            logger=process_logger,
            clock=clock,
        )

        for event in node_initialized_events:
            await attach_handler_saga.handle(event)

        completed_saga = await saga_repo.get_by_graph_execution_id(graph_execution_id_str)
        assert completed_saga is not None
        assert completed_saga.status == GraphExecutionSagaStatus.COMPLETED

        # ── 6. Verify links were created ──
        links = await link_exec_repo.list_by_graph_execution_id(
            initialized_event.graph_execution_id
        )
        assert len(links) == 2

    async def test_flow_with_no_links_fails_gracefully(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        fake_logger: FakeLogger,
    ) -> None:
        """Test that saga handles 0 linked nodes gracefully."""
        now = datetime.now(UTC)
        graph_id = GraphDefinitionId("empty-graph-id")

        graph = GraphDefinition.create(
            id=graph_id,
            name=GraphName("empty_graph"),
            purpose=Purpose("testing"),
            system_role=SystemRole.PLANNER,
            now=now,
        )
        await unit_of_work.repository(InMemoryGraphDefinitionRepository).save(graph)

        graph_execution_id = id_generator.new_id(GraphExecutionId)
        graph_execution = GraphExecution.initialize(
            id_=graph_execution_id,
            task_execution_id=TaskExecutionId("task-empty"),
            graph_definition_id=GraphDefinitionIdRef(graph_id.value),
            now=now,
        )
        async with unit_of_work:
            await unit_of_work.repository(InMemoryGraphExecutionRepository).save(graph_execution)
            unit_of_work.stage_events(graph_execution.pull_events())

        initialized_events = [
            e
            for e in unit_of_work.committed_events
            if isinstance(e, GraphExecutionInitializedEvent)
        ]
        assert len(initialized_events) == 1
        initialized_event = initialized_events[0]

        saga_repo = InMemoryGraphExecutionSagaRepository()
        saga = GraphExecutionSaga(repository=saga_repo)
        publisher = FakeCommandOutboxPublisher()

        link_def_repo = unit_of_work.repository(InMemoryNodeLinkDefinitionRepository)
        node_def_repo = unit_of_work.repository(InMemoryNodeDefinitionRepository)

        saga_handler = GraphExecutionInitializedHandler(
            saga_manager=saga,
            command_publisher=publisher,
            logger=FakeLogger(),
            link_definition_repository=link_def_repo,
            node_definition_repository=node_def_repo,
        )
        await saga_handler.handle(initialized_event)

        created_cmds = [
            (cmd_type, payload)
            for cmd_type, payload in publisher.published
            if cmd_type == "CreateNodeExecutionCommand"
        ]
        assert len(created_cmds) == 0
