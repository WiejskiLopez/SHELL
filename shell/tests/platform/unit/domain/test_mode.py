from __future__ import annotations

from shell.execution_service.domain.execution.aggregates.node_execution.value_objects.mode import (
    Mode,
)


class TestMode:
    def test_values(self) -> None:
        assert Mode.AGENT.value == "agent"
        assert Mode.ROUTER.value == "router"

    def test_str_enum(self) -> None:
        assert Mode("worker") == Mode.WORKER
