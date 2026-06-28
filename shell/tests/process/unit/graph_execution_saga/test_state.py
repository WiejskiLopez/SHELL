"""Unit tests for GraphExecutionSagaState and GraphExecutionSagaStatus."""

from __future__ import annotations

from shell.process.execution.graph_execution_saga.state import (
    GraphExecutionSagaState,
    GraphExecutionSagaStatus,
)


class TestGraphExecutionSagaStatus:
    def test_status_values(self) -> None:
        assert GraphExecutionSagaStatus.PENDING == "PENDING"
        assert GraphExecutionSagaStatus.COMPLETED == "COMPLETED"
        assert GraphExecutionSagaStatus.FAILED == "FAILED"

    def test_status_is_str_enum(self) -> None:
        assert GraphExecutionSagaStatus.PENDING.value == "PENDING"


class TestGraphExecutionSagaState:
    SAGA_ID = "saga-1"
    GRAPH_EXECUTION_ID = "ge-1"
    NODE_DEF_1 = "ndef-1"
    NODE_DEF_2 = "ndef-2"
    NODE_EXEC_1 = "nexec-1"
    NODE_EXEC_2 = "nexec-2"

    def test_initial_state(self) -> None:
        state = GraphExecutionSagaState(
            saga_id=self.SAGA_ID,
            graph_execution_id=self.GRAPH_EXECUTION_ID,
            expected_nodes_count=2,
        )
        assert state.saga_id == self.SAGA_ID
        assert state.graph_execution_id == self.GRAPH_EXECUTION_ID
        assert state.expected_nodes_count == 2
        assert state.graph_node_definition_executions == {}
        assert state.status == GraphExecutionSagaStatus.PENDING
        assert state.version == 1
        assert state.is_complete is False

    def test_record_node_execution_created_not_complete(self) -> None:
        state = GraphExecutionSagaState(
            saga_id=self.SAGA_ID,
            graph_execution_id=self.GRAPH_EXECUTION_ID,
            expected_nodes_count=2,
        )
        state.record_node_execution_created(self.NODE_DEF_1, self.NODE_EXEC_1)

        assert state.graph_node_definition_executions == {self.NODE_DEF_1: self.NODE_EXEC_1}
        assert state.is_complete is False
        assert state.status == GraphExecutionSagaStatus.PENDING

    def test_record_node_execution_created_completes(self) -> None:
        state = GraphExecutionSagaState(
            saga_id=self.SAGA_ID,
            graph_execution_id=self.GRAPH_EXECUTION_ID,
            expected_nodes_count=2,
        )
        state.record_node_execution_created(self.NODE_DEF_1, self.NODE_EXEC_1)
        state.record_node_execution_created(self.NODE_DEF_2, self.NODE_EXEC_2)

        assert state.graph_node_definition_executions == {
            self.NODE_DEF_1: self.NODE_EXEC_1,
            self.NODE_DEF_2: self.NODE_EXEC_2,
        }
        assert state.is_complete is True
        assert state.status == GraphExecutionSagaStatus.COMPLETED

    def test_record_node_execution_created_already_complete(self) -> None:
        state = GraphExecutionSagaState(
            saga_id=self.SAGA_ID,
            graph_execution_id=self.GRAPH_EXECUTION_ID,
            expected_nodes_count=1,
        )
        state.record_node_execution_created(self.NODE_DEF_1, self.NODE_EXEC_1)

        assert state.is_complete is True
        assert state.status == GraphExecutionSagaStatus.COMPLETED

        state.record_node_execution_created(self.NODE_DEF_2, self.NODE_EXEC_2)
        assert len(state.graph_node_definition_executions) == 2
        assert state.status == GraphExecutionSagaStatus.COMPLETED

    def test_is_complete_with_more_than_expected(self) -> None:
        state = GraphExecutionSagaState(
            saga_id=self.SAGA_ID,
            graph_execution_id=self.GRAPH_EXECUTION_ID,
            expected_nodes_count=1,
        )
        state.record_node_execution_created(self.NODE_DEF_1, self.NODE_EXEC_1)
        state.record_node_execution_created(self.NODE_DEF_2, self.NODE_EXEC_2)

        assert state.is_complete is True
        assert state.status == GraphExecutionSagaStatus.COMPLETED

    def test_zero_expected_nodes(self) -> None:
        state = GraphExecutionSagaState(
            saga_id=self.SAGA_ID,
            graph_execution_id=self.GRAPH_EXECUTION_ID,
            expected_nodes_count=0,
        )
        assert state.is_complete is True
        assert state.status == GraphExecutionSagaStatus.PENDING

    def test_version_starts_at_one(self) -> None:
        state = GraphExecutionSagaState(
            saga_id=self.SAGA_ID,
            graph_execution_id=self.GRAPH_EXECUTION_ID,
            expected_nodes_count=1,
        )
        assert state.version == 1
