"""NodeExecutionStrategy — port and 5 concrete implementations."""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.application.ports.ports import NodeProcessRunner
    from shell.domain.value_objects.execution_result import ExecutionResult


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
        from shell.domain.value_objects.manifest import Manifest
        from shell.domain.value_objects.mode import Mode

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
    from shell.domain.exceptions import InvalidNodeMode

    strategy = _STRATEGY_MAP.get(mode)
    if strategy is None:
        raise InvalidNodeMode(f"Unknown node mode: {mode!r}")
    return strategy
