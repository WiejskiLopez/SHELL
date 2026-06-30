"""Unit tests for GraphExecutionInitializedHandler."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

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
from shell.domain.execution.value_objects.graph_node_definition_id import (
    GraphNodeDefinitionId,
)
from shell.domain.platform.value_objects.created_at import CreatedAt
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


class FakeDefinitionProvider:
    async def get_graph_definition(self, definition_id: str) -> None:
        return None

    async def get_graph_definition_by_semantic_name(self, query: object) -> None:
        return None


class TestGraphExecutionInitializedHandler:
    NOW = datetime.now(tz=UTC)

    @pytest.fixture()
    def saga_manager(
        self, saga_repository: InMemoryGraphExecutionSagaRepository
    ) -> GraphExecutionSaga:
        return GraphExecutionSaga(repository=saga_repository)

    @pytest.fixture()
    def definition_provider(self) -> FakeDefinitionProvider:
        return FakeDefinitionProvider()

    @pytest.fixture()
    def handler(
        self,
        saga_manager: GraphExecutionSaga,
        command_publisher: FakeCommandOutboxPublisher,
        logger: FakeLogger,
        definition_provider: FakeDefinitionProvider,
    ) -> GraphExecutionInitializedHandler:
        return GraphExecutionInitializedHandler(
            saga_manager=saga_manager,
            command_publisher=command_publisher,
            logger=logger,
            definition_provider=definition_provider,
        )

    async def test_creates_saga_and_publishes_commands(
        self,
        handler: GraphExecutionInitializedHandler,
        saga_manager: GraphExecutionSaga,
        saga_repository: InMemoryGraphExecutionSagaRepository,
        command_publisher: FakeCommandOutboxPublisher,
    ) -> None:
        graph_execution_id = GraphExecutionId("ge-1")
        task_execution_id = TaskExecutionId("te-1")
        graph_definition_id = GraphDefinitionIdRef("gd-1")
        node_def_ids = (
            GraphNodeDefinitionId("ndef-1"),
            GraphNodeDefinitionId("ndef-2"),
            GraphNodeDefinitionId("ndef-3"),
        )

        event = GraphExecutionInitializedEvent(
            graph_execution_id=graph_execution_id,
            task_execution_id=task_execution_id,
            graph_definition_id=graph_definition_id,
            graph_node_definition_ids=node_def_ids,
            occurred_at=CreatedAt.from_datetime(self.NOW),
        )

        await handler.handle(event)

        stored = await saga_repository.get_by_graph_execution_id("ge-1")
        assert stored is not None
        assert stored.expected_nodes_count == 3
        assert stored.status.value == "PENDING"

        assert len(command_publisher.published) == 3
        for i, node_def_id in enumerate(node_def_ids):
            cmd_type, payload = command_publisher.published[i]
            assert cmd_type == "CreateGraphNodeExecutionCommand"
            assert payload["graph_execution_id"] == "ge-1"
            assert payload["graph_node_definition_id"] == node_def_id.value

    async def test_creates_saga_with_zero_nodes(
        self,
        handler: GraphExecutionInitializedHandler,
        saga_repository: InMemoryGraphExecutionSagaRepository,
        command_publisher: FakeCommandOutboxPublisher,
    ) -> None:
        graph_execution_id = GraphExecutionId("ge-empty")
        task_execution_id = TaskExecutionId("te-empty")
        graph_definition_id = GraphDefinitionIdRef("gd-empty")

        event = GraphExecutionInitializedEvent(
            graph_execution_id=graph_execution_id,
            task_execution_id=task_execution_id,
            graph_definition_id=graph_definition_id,
            graph_node_definition_ids=(),
            occurred_at=CreatedAt.from_datetime(self.NOW),
        )

        await handler.handle(event)

        stored = await saga_repository.get_by_graph_execution_id("ge-empty")
        assert stored is not None
        assert stored.expected_nodes_count == 0
        assert len(command_publisher.published) == 0
