"""Unit tests for GraphNodeExecutionInitializedHandler."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.execution.events import GraphNodeExecutionInitializedEvent
from shell.domain.execution.value_objects.graph_node_definition_id import GraphNodeDefinitionId
from shell.process.execution.graph_execution_saga.graph_execution_saga import (
    GraphExecutionSaga,
)
from shell.process.execution.graph_execution_saga.handlers.graph_node_execution_initialized_handler import (
    GraphNodeExecutionInitializedHandler,
)
from shell.tests.process.conftest import (
    FakeCommandOutboxPublisher,
    FakeLogger,
    InMemoryGraphExecutionSagaRepository,
)


class TestGraphNodeExecutionInitializedHandler:
    NOW = datetime.now(tz=UTC)

    @pytest.fixture()
    def saga_manager(
        self, saga_repository: InMemoryGraphExecutionSagaRepository
    ) -> GraphExecutionSaga:
        return GraphExecutionSaga(repository=saga_repository)

    @pytest.fixture()
    def handler(
        self,
        saga_manager: GraphExecutionSaga,
        command_publisher: FakeCommandOutboxPublisher,
        logger: FakeLogger,
    ) -> GraphNodeExecutionInitializedHandler:
        return GraphNodeExecutionInitializedHandler(
            saga_manager=saga_manager,
            command_publisher=command_publisher,
            logger=logger,
        )

    async def _create_saga(
        self,
        saga_manager: GraphExecutionSaga,
        graph_execution_id: str,
        expected_nodes_count: int,
    ) -> None:
        await saga_manager.create_saga(
            graph_execution_id=graph_execution_id,
            expected_nodes_count=expected_nodes_count,
        )

    async def test_records_node_and_publishes_attach_when_complete(
        self,
        handler: GraphNodeExecutionInitializedHandler,
        saga_manager: GraphExecutionSaga,
        saga_repository: InMemoryGraphExecutionSagaRepository,
        command_publisher: FakeCommandOutboxPublisher,
    ) -> None:
        await self._create_saga(saga_manager, "ge-1", expected_nodes_count=1)

        event = GraphNodeExecutionInitializedEvent(
            graph_execution_id=GraphExecutionId("ge-1"),
            node_id=GraphNodeExecutionId("gne-1"),
            parent_graph_execution_id=GraphExecutionId("ge-1"),
            node_definition_id=GraphNodeDefinitionId("ndef-1"),
            occurred_at=CreatedAt.from_datetime(self.NOW),
        )

        await handler.handle(event)

        stored = await saga_repository.get_by_graph_execution_id("ge-1")
        assert stored is not None
        assert stored.status.value == "COMPLETED"

        assert len(command_publisher.published) == 1
        cmd_type, payload = command_publisher.published[0]
        assert cmd_type == "AttachGraphNodeExecutionsCommand"
        assert payload["graph_execution_id"] == "ge-1"
        assert payload["graph_node_definition_executions"] == {"ndef-1": "gne-1"}

    async def test_does_not_publish_when_not_complete(
        self,
        handler: GraphNodeExecutionInitializedHandler,
        saga_manager: GraphExecutionSaga,
        command_publisher: FakeCommandOutboxPublisher,
    ) -> None:
        await self._create_saga(saga_manager, "ge-2", expected_nodes_count=2)

        event = GraphNodeExecutionInitializedEvent(
            graph_execution_id=GraphExecutionId("ge-2"),
            node_id=GraphNodeExecutionId("gne-1"),
            parent_graph_execution_id=GraphExecutionId("ge-2"),
            node_definition_id=GraphNodeDefinitionId("ndef-1"),
            occurred_at=CreatedAt.from_datetime(self.NOW),
        )

        await handler.handle(event)

        assert len(command_publisher.published) == 0

    async def test_publishes_attach_only_when_last_node_arrives(
        self,
        handler: GraphNodeExecutionInitializedHandler,
        saga_manager: GraphExecutionSaga,
        command_publisher: FakeCommandOutboxPublisher,
    ) -> None:
        await self._create_saga(saga_manager, "ge-3", expected_nodes_count=2)

        event_1 = GraphNodeExecutionInitializedEvent(
            graph_execution_id=GraphExecutionId("ge-3"),
            node_id=GraphNodeExecutionId("gne-1"),
            parent_graph_execution_id=GraphExecutionId("ge-3"),
            node_definition_id=GraphNodeDefinitionId("ndef-1"),
            occurred_at=CreatedAt.from_datetime(self.NOW),
        )
        await handler.handle(event_1)
        assert len(command_publisher.published) == 0

        event_2 = GraphNodeExecutionInitializedEvent(
            graph_execution_id=GraphExecutionId("ge-3"),
            node_id=GraphNodeExecutionId("gne-2"),
            parent_graph_execution_id=GraphExecutionId("ge-3"),
            node_definition_id=GraphNodeDefinitionId("ndef-2"),
            occurred_at=CreatedAt.from_datetime(self.NOW),
        )
        await handler.handle(event_2)

        assert len(command_publisher.published) == 1
        cmd_type, payload = command_publisher.published[0]
        assert cmd_type == "AttachGraphNodeExecutionsCommand"
        assert len(payload["graph_node_definition_executions"]) == 2

    async def test_handles_saga_not_found_gracefully(
        self,
        handler: GraphNodeExecutionInitializedHandler,
        command_publisher: FakeCommandOutboxPublisher,
    ) -> None:
        event = GraphNodeExecutionInitializedEvent(
            graph_execution_id=GraphExecutionId("nonexistent"),
            node_id=GraphNodeExecutionId("gne-1"),
            parent_graph_execution_id=GraphExecutionId("nonexistent"),
            node_definition_id=GraphNodeDefinitionId("ndef-1"),
            occurred_at=CreatedAt.from_datetime(self.NOW),
        )

        await handler.handle(event)

        assert len(command_publisher.published) == 0
