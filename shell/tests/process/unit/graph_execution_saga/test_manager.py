"""Unit tests for GraphExecutionSaga — pure state machine."""

from __future__ import annotations

import pytest
from shell.process.execution.graph_execution_saga.graph_execution_saga import (
    GraphExecutionSaga,
)
from shell.process.execution.graph_execution_saga.state import (
    GraphExecutionSagaStatus,
)
from shell.tests.process.conftest import (
    InMemoryGraphExecutionSagaRepository,
)


class TestGraphExecutionSaga:
    GRAPH_EXECUTION_ID = "ge-1"

    @pytest.fixture()
    def manager(
        self, saga_repository: InMemoryGraphExecutionSagaRepository
    ) -> GraphExecutionSaga:
        return GraphExecutionSaga(repository=saga_repository)

    async def test_create_saga(
        self,
        manager: GraphExecutionSaga,
        saga_repository: InMemoryGraphExecutionSagaRepository,
    ) -> None:
        saga = await manager.create_saga(
            graph_execution_id=self.GRAPH_EXECUTION_ID,
            expected_nodes_count=2,
        )

        assert saga.graph_execution_id == self.GRAPH_EXECUTION_ID
        assert saga.expected_nodes_count == 2
        assert saga.saga_id is not None
        assert saga.status == GraphExecutionSagaStatus.PENDING

        stored = await saga_repository.get_by_graph_execution_id(self.GRAPH_EXECUTION_ID)
        assert stored is not None
        assert stored.saga_id == saga.saga_id

    async def test_create_saga_persists_correctly(
        self,
        manager: GraphExecutionSaga,
        saga_repository: InMemoryGraphExecutionSagaRepository,
    ) -> None:
        saga = await manager.create_saga(
            graph_execution_id=self.GRAPH_EXECUTION_ID,
            expected_nodes_count=3,
        )

        stored = await saga_repository.get_by_graph_execution_id(self.GRAPH_EXECUTION_ID)
        assert stored is not None
        assert stored.expected_nodes_count == 3

    async def test_record_node_execution_while_pending(
        self,
        manager: GraphExecutionSaga,
        saga_repository: InMemoryGraphExecutionSagaRepository,
    ) -> None:
        await manager.create_saga(
            graph_execution_id=self.GRAPH_EXECUTION_ID,
            expected_nodes_count=2,
        )

        result = await manager.record_node_execution(
            graph_execution_id=self.GRAPH_EXECUTION_ID,
            node_definition_id="ndef-1",
            node_execution_id="nexec-1",
        )

        assert result is not None
        assert result.status == GraphExecutionSagaStatus.PENDING

    async def test_record_node_execution_completes_saga(
        self,
        manager: GraphExecutionSaga,
        saga_repository: InMemoryGraphExecutionSagaRepository,
    ) -> None:
        await manager.create_saga(
            graph_execution_id=self.GRAPH_EXECUTION_ID,
            expected_nodes_count=1,
        )

        result = await manager.record_node_execution(
            graph_execution_id=self.GRAPH_EXECUTION_ID,
            node_definition_id="ndef-1",
            node_execution_id="nexec-1",
        )

        assert result is not None
        assert result.status == GraphExecutionSagaStatus.COMPLETED
        assert result.is_complete is True

    async def test_record_node_execution_saga_not_found(
        self,
        manager: GraphExecutionSaga,
    ) -> None:
        result = await manager.record_node_execution(
            graph_execution_id="nonexistent",
            node_definition_id="ndef-1",
            node_execution_id="nexec-1",
        )

        assert result is None

    async def test_record_node_execution_after_completion_returns_saga(
        self,
        manager: GraphExecutionSaga,
        saga_repository: InMemoryGraphExecutionSagaRepository,
    ) -> None:
        await manager.create_saga(
            graph_execution_id=self.GRAPH_EXECUTION_ID,
            expected_nodes_count=1,
        )
        await manager.record_node_execution(
            graph_execution_id=self.GRAPH_EXECUTION_ID,
            node_definition_id="ndef-1",
            node_execution_id="nexec-1",
        )

        result = await manager.record_node_execution(
            graph_execution_id=self.GRAPH_EXECUTION_ID,
            node_definition_id="ndef-2",
            node_execution_id="nexec-2",
        )

        assert result is not None
        assert result.status == GraphExecutionSagaStatus.COMPLETED

    async def test_create_saga_unique_id_per_call(
        self,
        manager: GraphExecutionSaga,
    ) -> None:
        saga_1 = await manager.create_saga(
            graph_execution_id="ge-1",
            expected_nodes_count=1,
        )
        saga_2 = await manager.create_saga(
            graph_execution_id="ge-2",
            expected_nodes_count=1,
        )

        assert saga_1.saga_id != saga_2.saga_id
