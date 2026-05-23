from shell.utils.path.path import PathType
from __future__ import annotations


from shell.component.prompt_file.prompt_file import PromptFile
from shell.component.prompt.prompt.internal._init_prompt import _init_prompt
from shell.component.prompt.prompt_cli.prompt_cli import PromptCli
from shell.component.prompt.prompt_input.prompt_input import PromptInput
from shell.component.prompt.prompt_role.prompt_role import PromptRole
from shell.component.prompt.prompt_skill.prompt_skill import PromptSkill
from shell.component.prompt.prompt_system.prompt_system import PromptSystem
from shell.component.prompt.prompt_task.prompt_task import PromptTask


class Prompt:

    __slots__ = (
        "_app",
        "_file_prompts",
        "_prompt_dir",
        "_prompt_cli",
        "_prompt_input",
        "_prompt_role",
        "_prompt_skill",
        "_prompt_system",
        "_prompt_task",
    )

    def __init__(self, app) -> None:
        self._app = app
        self._file_prompts: list[PromptFile] = []
        self._prompt_dir: PathType | None = None
        self._prompt_cli: PromptCli | None = None
        self._prompt_input: PromptInput | None = None
        self._prompt_role: PromptRole | None = None
        self._prompt_skill: PromptSkill | None = None
        self._prompt_system: PromptSystem | None = None
        self._prompt_task: PromptTask | None = None

    @property
    def file_prompts_(self) -> list[PromptFile]:
        return self._file_prompts

    @property
    def prompt_dir_(self) -> PathType:
        return self._prompt_dir

    @property
    def prompt_cli_(self) -> PromptCli:
        if self._prompt_cli is None:
            self._prompt_cli = PromptCli(self._app)
        return self._prompt_cli

    @property
    def prompt_input_(self) -> PromptInput:
        if self._prompt_input is None:
            self._prompt_input = PromptInput(self._app)
        return self._prompt_input

    @property
    def prompt_role_(self) -> PromptRole:
        if self._prompt_role is None:
            self._prompt_role = PromptRole(self._app)
        return self._prompt_role

    @property
    def prompt_skill_(self) -> PromptSkill:
        if self._prompt_skill is None:
            self._prompt_skill = PromptSkill(self._app)
        return self._prompt_skill

    @property
    def prompt_system_(self) -> PromptSystem:
        if self._prompt_system is None:
            self._prompt_system = PromptSystem(self._app)
        return self._prompt_system

    @property
    def prompt_task_(self) -> PromptTask:
        if self._prompt_task is None:
            self._prompt_task = PromptTask(self._app)
        return self._prompt_task

    def init_prompt(self) -> None:
        _init_prompt(self)
