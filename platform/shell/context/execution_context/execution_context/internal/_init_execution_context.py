from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.context.execution_context.execution_context.execution_context import ExecutionContext


def _init_execution_context(execution_context: ExecutionContext) -> None:
    execution_context._task = ""
    execution_context._input = {}
    execution_context._expected_output = ""
    execution_context._constraints = []
