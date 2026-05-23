"""prompt_skill.py
PromptSkill — holds a list of PromptFile objects loaded from skill prompt files.

Slots:
    _file_prompts — list of PromptFile objects loaded from *.<task-name>.skill.prompt.md files
"""

from __future__ import annotations

from shell.component.prompt_file.prompt_file import PromptFile
from shell.component.prompt.prompt_skill.internal._init_prompt_skill import _init_prompt_skill
from shell.component.prompt.prompt_skill.internal._prompt import _prompt


class PromptSkill:
    """Holds skill prompts loaded from *.<task-name>.skill.prompt.md files in task-dir."""

    __slots__ = ("_app", "_file_prompts")

    def __init__(self, app=None) -> None:
        self._app = app
        self._file_prompts: list[PromptFile] = []

    @property
    def file_prompts_(self) -> list[PromptFile]:
        return self._file_prompts

    def init_prompt_skill(self) -> None:
        _init_prompt_skill(self)

    def prompt(self) -> str:
        return _prompt(self)
