"""Entry point for Agent command construction and execution."""

from __future__ import annotations

from collections.abc import Callable
from subprocess import CompletedProcess

from shell.module.agent.agent.internal._init_agent import _init_agent
from shell.module.agent.agent.internal._run_agent import _run_agent
from shell.module.agent.agent_prompt.agent_prompt import AgentPrompt
from shell.module.agent.agent_properties.agent_properties import AgentProperties


class Agent:
    """
    Slots:
        _app              — parent App
        _which            — Optional; injectable shutil.which replacement
        _os_name          — Optional; injectable os.name replacement
        _agent_prompt     — AgentPrompt
        _agent_properties — AgentProperties
    """

    __slots__ = ("_app", "_which", "_os_name", "_agent_prompt", "_agent_properties")

    def __init__(self, app, which=None, os_name=None) -> None:
        self._app = app
        self._which = which
        self._os_name = os_name
        self._agent_prompt: AgentPrompt | None = None
        self._agent_properties: AgentProperties | None = None

    @property
    def which_(self):
        return self._which

    @property
    def os_name_(self):
        return self._os_name

    @property
    def agent_prompt_(self) -> AgentPrompt:
        if self._agent_prompt is None:
            self._agent_prompt = AgentPrompt(self._app)
        return self._agent_prompt

    @property
    def agent_properties_(self) -> AgentProperties:
        if self._agent_properties is None:
            self._agent_properties = AgentProperties(self._app)
        return self._agent_properties

    def init_agent(self) -> None:
        _init_agent(self)

    def run_agent(
        self,
        runner: Callable[..., CompletedProcess] | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        _run_agent(self, runner=runner, sleep=sleep)
