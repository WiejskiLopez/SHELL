"""_assert_prompt_dir_exists.py
Validate that the prompt directory exists and is a directory.
"""

from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_prompt_dir_exists(prompt_dir: PathType) -> None:
    if not Path.is_dir(Path.new(prompt_dir)):
        raise ValueError(f"Prompt directory does not exist or is not a directory: {prompt_dir}")
