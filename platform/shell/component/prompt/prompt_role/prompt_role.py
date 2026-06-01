"""prompt_role.py
PromptRole — holds a list of PromptFile objects loaded from role prompt files.

Slots:
    _file_prompts — list of PromptFile objects loaded from *.<role>.prompt.md files
"""

from __future__ import annotations

from shell.component.prompt_file.prompt_file import PromptFile
from shell.component.prompt.prompt_role.internal._init_prompt_role import _init_prompt_role
from shell.component.prompt.prompt_role.internal._prompt import _prompt


class PromptRole:
    """Holds role prompts loaded from *.<role>.prompt.md files in task-dir."""

    __slots__ = ("_app", "_file_prompts")

    def __init__(self, app=None) -> None:
        self._app = app
        self._file_prompts: list[PromptFile] = []

    @property
    def file_prompts_(self) -> list[PromptFile]:
        return self._file_prompts

    def init_prompt_role(self) -> None:
        _init_prompt_role(self)

    def prompt(self) -> str:
        return _prompt(self)
