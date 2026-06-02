from __future__ import annotations



from shell.component.prompt_file.internal._init_prompt_file import _init_prompt_file
from shell.component.prompt.prompt_type.prompt_type import PromptType


class PromptFile:
    """Represents a single prompt file (DB-sourced; no disk I/O)."""

    __slots__ = ("_file_name", "_file_body", "_prompt_type")

    def __init__(self) -> None:
        self._file_name: str = ""
        self._file_body: str = ""
        self._prompt_type: PromptType = PromptType.NONE

    @property
    def file_name_(self) -> str:
        return self._file_name

    @property
    def file_body_(self) -> str:
        return self._file_body

    @property
    def prompt_type_(self) -> PromptType:
        return self._prompt_type

    def init_prompt_file(self, file_name: str, file_body: str) -> None:
        _init_prompt_file(self, file_name, file_body)
