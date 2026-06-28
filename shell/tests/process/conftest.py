"""Fixtures for process layer tests — in-memory saga repository + fake command publisher."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest
from shell.process.execution.graph_execution_saga.state import (
    GraphExecutionSagaState,
)


class InMemoryGraphExecutionSagaRepository:
    def __init__(self) -> None:
        self._store: dict[str, GraphExecutionSagaState] = {}

    async def save(self, saga: GraphExecutionSagaState) -> None:
        self._store[saga.graph_execution_id] = saga

    async def get_by_graph_execution_id(
        self, graph_execution_id: str,
    ) -> GraphExecutionSagaState | None:
        return self._store.get(graph_execution_id)


class FakeCommandOutboxPublisher:
    def __init__(self) -> None:
        self.published: list[tuple[str, dict[str, Any]]] = []

    async def publish(
        self,
        command_type: str,
        payload: dict[str, Any],
        occurred_at: datetime | None = None,
    ) -> None:
        self.published.append((command_type, payload))


class FakeLogger:
    def debug(self, msg: str, **kw: object) -> None:
        pass

    def info(self, msg: str, **kw: object) -> None:
        pass

    def warning(self, msg: str, **kw: object) -> None:
        pass

    def error(self, msg: str, **kw: object) -> None:
        pass


@pytest.fixture()
def saga_repository() -> InMemoryGraphExecutionSagaRepository:
    return InMemoryGraphExecutionSagaRepository()


@pytest.fixture()
def command_publisher() -> FakeCommandOutboxPublisher:
    return FakeCommandOutboxPublisher()


@pytest.fixture()
def logger() -> FakeLogger:
    return FakeLogger()
