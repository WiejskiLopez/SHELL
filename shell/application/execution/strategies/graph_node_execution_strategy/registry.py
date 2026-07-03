from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.execution.strategies.graph_node_execution_strategy.agent_strategy import (
    AgentStrategy,
)
from shell.application.execution.strategies.graph_node_execution_strategy.planner_strategy import (
    PlannerStrategy,
)
from shell.application.execution.strategies.graph_node_execution_strategy.router_strategy import (
    RouterStrategy,
)
from shell.application.execution.strategies.graph_node_execution_strategy.tasker_strategy import (
    TaskerStrategy,
)
from shell.application.execution.strategies.graph_node_execution_strategy.tool_strategy import (
    ToolStrategy,
)
from shell.application.execution.strategies.graph_node_execution_strategy.worker_strategy import (
    WorkerStrategy,
)

if TYPE_CHECKING:
    from shell.application.execution.strategies.graph_node_execution_strategy.protocol import (
        GraphNodeExecutionStrategy,  # noqa: TC002 — GraphNodeExecutionStrategy używany w słowniku _STRATEGY_MAP i sygnaturze get_strategy()
    )

_STRATEGY_MAP: dict[str, GraphNodeExecutionStrategy] = {
    "agent": AgentStrategy(),
    "planner": PlannerStrategy(),
    "router": RouterStrategy(),
    "tasker": TaskerStrategy(),
    "tool": ToolStrategy(),
    "worker": WorkerStrategy(),
}


def get_strategy(mode: str) -> GraphNodeExecutionStrategy:
    strategy = _STRATEGY_MAP.get(mode)
    if strategy is None:
        raise InvalidNodeMode(f"Unknown node mode: {mode!r}")
    return strategy
