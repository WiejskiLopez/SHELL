"""process.py
Process: wrapper for a single subprocess invocation.

Slots:
    _process_command — ProcessCommand; the command to execute
    _runner          — Callable; subprocess runner (default: subprocess.run)
    _returncode      — int; exit code of the process
    _stdout          — str; captured stdout
    _stderr          — str; captured stderr
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable

from shell.component.process.process_command.process_command import ProcessCommand
from shell.component.process.process.internal._init_process import _init_process
from shell.component.process.process.internal._run_process import _run_process


class Process:
    """Represents a single subprocess invocation and its result."""

    __slots__ = ("_process_command", "_runner", "_returncode", "_stdout", "_stderr")

    def __init__(self) -> None:
        self._process_command: ProcessCommand | None = None
        self._runner: Callable[..., subprocess.CompletedProcess] = subprocess.run
        self._returncode: int | None = None
        self._stdout: str | None = None
        self._stderr: str | None = None

    @property
    def process_command_(self) -> ProcessCommand:
        if self._process_command is None:
            self._process_command = ProcessCommand()
        return self._process_command

    def init_process(self) -> None:
        _init_process(self)

    def run_process(self, cwd: str) -> None:
        _run_process(self, cwd)
