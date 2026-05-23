"""agent_prompt.py
AgentPrompt: single entry point for prompt state for a single node run.

Fields (own):
    _app            — parent App (DOM back-reference)
    _prompt_cli     — CLI prompt (PromptCli | None)
    _prompt_role    — role prompts loaded from task-dir (PromptRole | None)
    _prompt_skill   — skill prompts loaded from source-dir (PromptSkill | None)
    _prompt_system  — system prompts loaded from task-dir (PromptSystem | None)

Properties:
    prompt_cli_     — lazy PromptCli instance
    prompt_role_    — lazy PromptRole instance
    prompt_skill_   — lazy PromptSkill instance
    prompt_system_  — lazy PromptSystem instance
"""

from __future__ import annotations

from shell.module.agent.agent_prompt.internal._init_agent_prompt import _init_agent_prompt
from shell.module.agent.agent_prompt.internal._build_prompt_from_input import _build_prompt_from_input
from shell.component.prompt.prompt_cli.prompt_cli import PromptCli
from shell.component.prompt.prompt_role.prompt_role import PromptRole
from shell.component.prompt.prompt_skill.prompt_skill import PromptSkill
from shell.component.prompt.prompt_system.prompt_system import PromptSystem


class AgentPrompt:
    """Manages prompt state for a single node run.

    Constructed as AgentPrompt(app). Call init_agent_prompt() to populate from app.
    """

    __slots__ = ("_app", "_prompt_cli", "_prompt_role", "_prompt_skill", "_prompt_system")

    def __init__(self, app=None) -> None:
        self._app = app
        self._prompt_cli: PromptCli | None = None
        self._prompt_role: PromptRole | None = None
        self._prompt_skill: PromptSkill | None = None
        self._prompt_system: PromptSystem | None = None

    @property
    def prompt_cli_(self) -> PromptCli:
        if self._prompt_cli is None:
            self._prompt_cli = PromptCli()
        return self._prompt_cli

    @property
    def prompt_role_(self) -> PromptRole:
        if self._prompt_role is None:
            self._prompt_role = PromptRole()
        return self._prompt_role

    @property
    def prompt_skill_(self) -> PromptSkill:
        if self._prompt_skill is None:
            self._prompt_skill = PromptSkill()
        return self._prompt_skill

    @property
    def prompt_system_(self) -> PromptSystem:
        if self._prompt_system is None:
            self._prompt_system = PromptSystem()
        return self._prompt_system

    # -----------------------------------------------------------------------
    # DOM operation
    # -----------------------------------------------------------------------

    def init_agent_prompt(self) -> None:
        _init_agent_prompt(self)

    def prompt(self) -> str:
        cli_body = self._prompt_cli.prompt_file_.file_body_ if self._prompt_cli is not None else None
        if cli_body:
            return cli_body
        parts = [self._prompt_role.prompt(), self._prompt_skill.prompt(), self._prompt_system.prompt()]
        base = "\n\n".join(p for p in parts if p)
        input_section = _build_prompt_from_input(self._app)
        if input_section:
            return base + "\n\n" + input_section if base else input_section
        return base
