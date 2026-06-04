"""process.py
Process: wrapper for a single subprocess invocation.

Slots:
    _app             — parent app
    _process_command — ProcessCommand; all subprocess parameters
    _runner          — Callable; subprocess runner (default: subprocess.run)
    _returncode      — int; exit code of the process
    _stdout          — str; captured stdout
    _stderr          — str; captured stderr
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable

from shell.component.process.process_command.process_command import ProcessCommand
from shell.component.process.process.internal._run_process import _run_process
from shell.component.process.process.internal._init_process_agent import _init_process_agent
from shell.component.process.process.internal._init_process_worker import _init_process_worker
from shell.component.process.process.internal._init_process_tool import _init_process_tool
from shell.component.process.process.internal._init_process_sub_node import _init_process_sub_node


class Process:
    """Represents a single subprocess invocation and its result."""

    __slots__ = ("_app", "_process_command", "_runner", "_returncode", "_stdout", "_stderr")

    def __init__(self, app, runner: Callable[..., subprocess.CompletedProcess] | None = None) -> None:
        self._app = app
        self._process_command: ProcessCommand | None = None
        self._runner: Callable[..., subprocess.CompletedProcess] = runner if runner is not None else subprocess.run
        self._returncode: int | None = None
        self._stdout: str | None = None
        self._stderr: str | None = None

    @property
    def app_(self):
        return self._app

    @property
    def process_command_(self) -> ProcessCommand:
        if self._process_command is None:
            self._process_command = ProcessCommand()
        return self._process_command

    @property
    def returncode_(self) -> int | None:
        return self._returncode

    @property
    def stdout_(self) -> str | None:
        return self._stdout

    @property
    def stderr_(self) -> str | None:
        return self._stderr

    def init_process_agent(self, prompt: str, timeout: int, which=None, os_name=None) -> None:
        _init_process_agent(self, prompt, timeout, which, os_name)

    def init_process_worker(self) -> None:
        _init_process_worker(self)

    def init_process_tool(self) -> None:
        _init_process_tool(self)

    def init_process_sub_node(self, sub_node, task_dir, python_exe=None) -> None:
        _init_process_sub_node(self, sub_node, task_dir, python_exe)

    def run_process(self) -> None:
        _run_process(self)
