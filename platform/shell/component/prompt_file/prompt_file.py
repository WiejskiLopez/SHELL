"""prompt_file.py
PromptFile — represents a single prompt file loaded from disk.

Slots:
    _file_name    — file name (str)
    _file_body    — file content (str)
    _prompt_type  — prompt type derived from file name (str)
"""

from __future__ import annotations

from shell.utils.path.path import PathType



from shell.component.prompt_file.internal._init_prompt_file import _init_prompt_file
from shell.component.prompt_file.internal._save_prompt_file import _save_prompt_file
from shell.component.prompt.prompt_type.prompt_type import PromptType


class PromptFile:
    """Represents a single prompt file.

    Slots:
        _file_name    — file name (str)
        _file_body    — file content (str)
        _prompt_type  — prompt type derived from file name (str)
    """

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

    def init_prompt_file(self, file_name: str, file_body: str, save_dir: PathType) -> None:
        _init_prompt_file(self, file_name, file_body, save_dir)

    def save_prompt_file(self, save_dir) -> None:
        _save_prompt_file(self, save_dir)
