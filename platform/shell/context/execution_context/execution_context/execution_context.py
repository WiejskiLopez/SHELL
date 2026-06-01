"""execution_context.py
ExecutionContext — sub-task execution context: what to do right now.

Slots:
    _task        — name of the task to execute
    _input       — input data for the task
    _expected_output — description of expected output
    _constraints — list of constraints for this execution
"""

from __future__ import annotations

from shell.context.execution_context.execution_context.internal._init_execution_context import _init_execution_context


class ExecutionContext:
    """Sub-task execution context.

    Slots:
        _task            — name of the task to execute
        _input           — input data for the task
        _expected_output — description of expected output
        _constraints     — list of constraints for this execution
    """

    __slots__ = ("_task", "_input", "_expected_output", "_constraints")

    def __init__(self) -> None:
        self._task: str = ""
        self._input: dict = {}
        self._expected_output: str = ""
        self._constraints: list[str] = []

    @property
    def task_(self) -> str:
        return self._task

    @property
    def input_(self) -> dict:
        return self._input

    @property
    def expected_output_(self) -> str:
        return self._expected_output

    @property
    def constraints_(self) -> list[str]:
        return self._constraints

    def init_execution_context(self) -> None:
        _init_execution_context(self)
