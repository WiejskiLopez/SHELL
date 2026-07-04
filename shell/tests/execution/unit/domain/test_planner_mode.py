"""Tests for PLANNER mode enum and strategy."""

from __future__ import annotations

from shell.application.execution.strategies.node_execution_strategy import (
    PlannerStrategy,
    get_strategy,
)
from shell.domain.platform.value_objects.mode import Mode


class TestPlannerMode:
    def test_planner_mode_exists(self) -> None:
        assert Mode.PLANNER.value == "planner"

    def test_planner_strategy_registered(self) -> None:
        strategy = get_strategy("planner")
        assert isinstance(strategy, PlannerStrategy)
        assert strategy.mode == Mode.PLANNER

    def test_planner_strategy_not_none(self) -> None:
        strategy = get_strategy("planner")
        assert strategy is not None
