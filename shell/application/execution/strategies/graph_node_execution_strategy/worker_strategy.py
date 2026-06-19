from __future__ import annotations

from shell.application.execution.strategies.graph_node_execution_strategy._base_strategy import (
    _BaseStrategy,
)


class WorkerStrategy(_BaseStrategy):
    mode = "worker"
