from __future__ import annotations

from shell.component.prompt_file.prompt_file import PromptFile
from shell.component.prompt.prompt_input.internal._init_prompt_input import _init_prompt_input
from shell.component.prompt.prompt_input.internal._prompt import _prompt


class PromptInput:

    __slots__ = ("_app", "_file_prompts")

    def __init__(self, app=None) -> None:
        self._app = app
        self._file_prompts: list[PromptFile] = []

    @property
    def file_prompts_(self) -> list[PromptFile]:
        return self._file_prompts

    def init_prompt_input(self) -> None:
        _init_prompt_input(self)

    def prompt(self) -> str:
        return _prompt(self)
