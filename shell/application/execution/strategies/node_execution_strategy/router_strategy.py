from __future__ import annotations

from shell.application.execution.strategies.node_execution_strategy._base_strategy import (
    _BaseStrategy,
)


class RouterStrategy(_BaseStrategy):
    mode = "router"
