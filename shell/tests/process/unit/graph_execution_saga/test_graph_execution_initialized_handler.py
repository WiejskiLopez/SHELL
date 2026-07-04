"""Unit tests for GraphExecutionInitializedHandler."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

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
from shell.domain.definition.value_objects.node_position import NodePosition
from shell.domain.definition.value_objects.node_role_name import NodeRoleName
from shell.domain.definition.value_objects.node_type_name import NodeTypeName
from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.domain.execution.events import GraphExecutionInitializedEvent
from shell.domain.execution.value_objects.graph_definition_id import (
    GraphDefinitionIdRef,
)
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.mode import Mode
from shell.process.execution.graph_execution_saga.graph_execution_saga import (
    GraphExecutionSaga,
)
from shell.process.execution.graph_execution_saga.handlers.graph_execution_initialized_handler import (
    GraphExecutionInitializedHandler,
)

if TYPE_CHECKING:
    from shell.tests.process.conftest import (
        FakeCommandOutboxPublisher,
        FakeLogger,
        InMemoryGraphExecutionSagaRepository,
    )


from shell.infrastructure.definition.persistence.memory.in_memory_node_definition_repository import (
            InMemoryNodeDefinitionRepository,
        )
from shell.infrastructure.definition.persistence.memory.in_memory_node_link_definition_repository import (
            InMemoryNodeLinkDefinitionRepository,
        )
class TestGraphExecutionInitializedHandler:
    NOW = datetime.now(tz=UTC)

    @pytest.fixture()
    def saga_manager(
        self, saga_repository: InMemoryGraphExecutionSagaRepository
    ) -> GraphExecutionSaga:
        return GraphExecutionSaga(repository=saga_repository)

    @pytest.fixture()
    def link_def_repo(self) -> object:
        return InMemoryNodeLinkDefinitionRepository()

    @pytest.fixture()
    def node_def_repo(self) -> object:
        return InMemoryNodeDefinitionRepository()

    @pytest.fixture()
    def handler(
        self,
        saga_manager: GraphExecutionSaga,
        command_publisher: FakeCommandOutboxPublisher,
        logger: FakeLogger,
        link_def_repo,
        node_def_repo,
    ) -> GraphExecutionInitializedHandler:
        return GraphExecutionInitializedHandler(
            saga_manager=saga_manager,
            command_publisher=command_publisher,
            logger=logger,
            link_definition_repository=link_def_repo,
            node_definition_repository=node_def_repo,
        )

    async def test_creates_saga_and_publishes_zero_commands_when_no_links(
        self,
        handler: GraphExecutionInitializedHandler,
        saga_manager: GraphExecutionSaga,
        saga_repository: InMemoryGraphExecutionSagaRepository,
        command_publisher: FakeCommandOutboxPublisher,
        link_def_repo,
    ) -> None:
        graph_execution_id = GraphExecutionId("ge-1")
        task_execution_id = TaskExecutionId("te-1")
        graph_definition_id = GraphDefinitionIdRef("gd-1")

        event = GraphExecutionInitializedEvent.now(
            graph_execution_id=graph_execution_id,
            task_execution_id=task_execution_id,
            graph_definition_id=graph_definition_id,
            now=CreatedAt.from_datetime(self.NOW),
        )

        await handler.handle(event)

        saga = await saga_repository.get_by_graph_execution_id(graph_execution_id.value)
        assert saga is not None
        assert saga.expected_nodes_count == 0

        published_commands = [
            cmd_type for cmd_type, _ in command_publisher.published
        ]
        assert "CreateNodeExecutionCommand" not in published_commands

    async def test_creates_saga_and_publishes_commands_for_linked_nodes(
        self,
        handler: GraphExecutionInitializedHandler,
        saga_manager: GraphExecutionSaga,
        saga_repository: InMemoryGraphExecutionSagaRepository,
        command_publisher: FakeCommandOutboxPublisher,
        link_def_repo,
        node_def_repo,
    ) -> None:
        graph_execution_id = GraphExecutionId("ge-2")
        task_execution_id = TaskExecutionId("te-2")
        graph_definition_id_ref = GraphDefinitionIdRef("gd-2")
        graph_definition_id = GraphDefinitionId("gd-2")

        node_def = NodeDefinition.create(
            id=NodeDefinitionId("ndef-1"),
            position=NodePosition(0),
            mode=Mode("agent"),
            role=NodeRoleName("AGENT"),
            node_type=NodeTypeName("agent"),
        )
        await node_def_repo.save(node_def)

        link = NodeLinkDefinition(
            id=NodeLinkDefinitionId.generate(),
            graph_definition_id=graph_definition_id,
            node_definition_id=node_def.id,
        )
        await link_def_repo.save(link)

        event = GraphExecutionInitializedEvent.now(
            graph_execution_id=graph_execution_id,
            task_execution_id=task_execution_id,
            graph_definition_id=graph_definition_id_ref,
            now=CreatedAt.from_datetime(self.NOW),
        )

        await handler.handle(event)

        saga = await saga_repository.get_by_graph_execution_id(graph_execution_id.value)
        assert saga is not None
        assert saga.expected_nodes_count == 1

        published = [
            (cmd_type, payload)
            for cmd_type, payload in command_publisher.published
            if cmd_type == "CreateNodeExecutionCommand"
        ]
        assert len(published) == 1
        _, payload = published[0]
        assert payload["graph_execution_id"] == "ge-2"
        assert payload["node_definition_id"] == "ndef-1"
