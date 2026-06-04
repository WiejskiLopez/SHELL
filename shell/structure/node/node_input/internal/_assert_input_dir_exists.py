"""_assert_input_dir_exists.py
Validate that the input directory exists and is a directory.
"""

from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_input_dir_exists(input_dir: PathType) -> None:
    if not Path.is_dir(input_dir):
        raise ValueError(f"Input directory does not exist or is not a directory: {input_dir}")
