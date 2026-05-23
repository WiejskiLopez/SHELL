"""prompt_cli.py
PromptCli — holds the CLI-sourced prompt for a single agent run.

Slots:
    _prompt_file — PromptFile built from CLI --prompt arg (PromptFile | None)
"""

from __future__ import annotations

from shell.component.prompt_file.prompt_file import PromptFile
from shell.component.prompt.prompt_cli.internal._init_prompt_cli import _init_prompt_cli


class PromptCli:
    """Holds the CLI-sourced prompt for a single agent run."""

    __slots__ = ("_app", "_prompt_file")

    def __init__(self, app=None) -> None:
        self._app = app
        self._prompt_file: PromptFile | None = None

    @property
    def prompt_file_(self) -> PromptFile:
        if self._prompt_file is None:
            self._prompt_file = PromptFile()
        return self._prompt_file

    def init_prompt_cli(self) -> None:
        _init_prompt_cli(self)
