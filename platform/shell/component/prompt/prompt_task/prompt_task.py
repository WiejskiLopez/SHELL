from __future__ import annotations

from shell.component.prompt_file.prompt_file import PromptFile
from shell.component.prompt.prompt_task.internal._init_prompt_task import _init_prompt_task
from shell.component.prompt.prompt_task.internal._prompt import _prompt


class PromptTask:

    __slots__ = ("_app", "_file_prompts")

    def __init__(self, app=None) -> None:
        self._app = app
        self._file_prompts: list[PromptFile] = []

    @property
    def file_prompts_(self) -> list[PromptFile]:
        return self._file_prompts

    def init_prompt_task(self) -> None:
        _init_prompt_task(self)

    def prompt(self) -> str:
        return _prompt(self)
