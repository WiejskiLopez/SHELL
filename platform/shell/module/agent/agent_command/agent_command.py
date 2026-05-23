"""agent_command.py
AgentCommand — responsible for assembling the Copilot CLI command.
"""

from __future__ import annotations

from shell.module.agent.agent_command.internal._init_agent_command import _init_agent_command
from shell.component.command.command import Command


class AgentCommand:
    """Builds the Copilot CLI command argument list."""

    __slots__ = ("_app", "_which", "_os_name", "_command")

    def __init__(self, app, which=None, os_name=None) -> None:
        self._app = app
        self._which = which
        self._os_name = os_name
        self._command: Command | None = None

    @property
    def command_(self) -> Command:
        if self._command is None:
            self._command = Command([])
        return self._command

    def init_agent_command(self) -> None:
        _init_agent_command(self)
