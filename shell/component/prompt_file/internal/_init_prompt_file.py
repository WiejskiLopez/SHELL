
from __future__ import annotations

from shell.component.prompt.prompt_type.prompt_type import PromptType


def _init_prompt_file(prompt_file, file_name: str, file_body: str) -> None:
    prompt_file._file_name = file_name
    prompt_file._file_body = file_body
    if '.system.' in file_name:
        prompt_file._prompt_type = PromptType.SYSTEM
    elif '.role.' in file_name or file_name.endswith('.prompt.md'):
        prompt_file._prompt_type = PromptType.ROLE
    else:
        prompt_file._prompt_type = PromptType.NONE
