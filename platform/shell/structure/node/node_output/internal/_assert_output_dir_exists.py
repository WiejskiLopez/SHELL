"""_assert_output_dir_exists.py
Validate that the output directory exists and is a directory.
"""

from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_output_dir_exists(output_dir: PathType) -> None:
    if not Path.is_dir(output_dir):
        raise ValueError(f"Output directory does not exist or is not a directory: {output_dir}")
