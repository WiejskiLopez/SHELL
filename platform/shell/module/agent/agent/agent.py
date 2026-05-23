"""Entry point for Agent command construction and execution."""

from __future__ import annotations

from collections.abc import Callable
from subprocess import CompletedProcess

from shell.module.agent.agent.internal._init_agent import _init_agent
from shell.module.agent.agent.internal._run_agent import _run_agent
from shell.module.agent.agent_command.agent_command import AgentCommand
from shell.module.agent.agent_prompt.agent_prompt import AgentPrompt
from shell.module.agent.agent_properties.agent_properties import AgentProperties


class Agent:
    __slots__ = ("_app","_agent_command", "_agent_prompt", "_agent_properties")

    def __init__(self, app, which=None, os_name=None) -> None:
        self._app = app
        self._agent_command: AgentCommand = AgentCommand(app, which, os_name)
        self._agent_prompt: AgentPrompt = AgentPrompt(app)
        self._agent_properties: AgentProperties = AgentProperties(app)

    # -----------------------------------------------------------------------
    # Slot properties
    # -----------------------------------------------------------------------

    @property
    def agent_command_(self) -> AgentCommand:
        return self._agent_command

    @property
    def agent_prompt_(self) -> AgentPrompt:
        return self._agent_prompt

    @property
    def agent_properties_(self) -> AgentProperties:
        return self._agent_properties

    def init_agent(self) -> None:
        _init_agent(self)

    def run_agent(
        self,
        runner: Callable[..., CompletedProcess] | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        _run_agent(self, runner=runner, sleep=sleep)
