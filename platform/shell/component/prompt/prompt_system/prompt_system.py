"""prompt_system.py
PromptSystem — holds system prompt list loaded from task-dir.

Slots:
    _file_prompts — list of PromptFile objects (PromptFile)

Loads files matching *.system.prompt.md:
    - <nr>.<role>.system.prompt.md — only if role matches current role
    - <nr>.system.prompt.md        — always loaded (no role indicator)
"""

from __future__ import annotations

from shell.component.prompt_file.prompt_file import PromptFile
from shell.component.prompt.prompt_system.internal._init_prompt_system import _init_prompt_system
from shell.component.prompt.prompt_system.internal._prompt import _prompt


class PromptSystem:
    """Holds system prompts loaded from *.system.prompt.md files in task-dir."""

    __slots__ = ("_app", "_file_prompts")

    def __init__(self, app=None) -> None:
        self._app = app
        self._file_prompts: list[FilePrompt] = []

    @property
    def file_prompts_(self) -> list[FilePrompt]:
        return self._file_prompts

    def init_prompt_system(self) -> None:
        _init_prompt_system(self)

    def prompt(self) -> str:
        return _prompt(self)
