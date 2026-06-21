"""Deprecated — use planner_result_handler.PlannerResultHandler instead.

This stub re-exports the refactored handler for backward compatibility.
"""

from __future__ import annotations

from shell.application.execution.event_handlers.planner_result_handler import (
    PlannerResultHandler,
)

SpawnSubGraphsOnPlannerCompletionHandler = PlannerResultHandler

__all__ = [
    "SpawnSubGraphsOnPlannerCompletionHandler",
]
