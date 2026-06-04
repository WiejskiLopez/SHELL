"""process_command.py
ProcessCommand: holds all parameters for a single subprocess invocation.

Slots:
    _cmd     — list[str]; the CLI command arguments
    _stdin   — str | None; text piped to process stdin (optional)
    _timeout — int | None; seconds before TimeoutExpired (optional)
    _cwd     — str; working directory for the process
    _env     — dict | None; environment variables override (optional)
"""

from __future__ import annotations

from shell.component.process.process_command.internal._init_process_command import _init_process_command
from shell.component.process.process_command.internal._init_process_command_agent import _init_process_command_agent
from shell.component.process.process_command.internal._init_process_command_sub_node import _init_process_command_sub_node


class ProcessCommand:
    """Holds all subprocess parameters for a single Process invocation."""

    __slots__ = ("_cmd", "_stdin", "_timeout", "_cwd", "_env")

    def __init__(self) -> None:
        self._cmd: list[str] | None = None
        self._stdin: str | None = None
        self._timeout: int | None = None
        self._cwd: str | None = None
        self._env: dict | None = None

    @property
    def cmd_(self) -> list[str]:
        return self._cmd

    @property
    def stdin_(self) -> str | None:
        return self._stdin

    @property
    def timeout_(self) -> int | None:
        return self._timeout

    @property
    def cwd_(self) -> str:
        return self._cwd

    @property
    def env_(self) -> dict | None:
        return self._env

    def init_process_command(self, cmd: list[str], cwd: str, stdin: str | None = None, timeout: int | None = None, env: dict | None = None) -> None:
        _init_process_command(self, cmd, cwd, stdin, timeout, env)

    def init_process_command_agent(self, app, prompt: str, timeout: int, which=None, os_name=None) -> None:
        _init_process_command_agent(self, app, prompt, timeout, which, os_name)

    def init_process_command_sub_node(self, sub_node, task_dir, app, python_exe=None) -> None:
        _init_process_command_sub_node(self, sub_node, task_dir, app, python_exe)
