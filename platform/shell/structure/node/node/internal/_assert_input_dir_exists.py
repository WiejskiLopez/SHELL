"""_assert_input_dir_exists.py
Responsible for one thing: raising FileNotFoundError when the node input/ directory is missing.
"""

from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_input_dir_exists(path: PathType) -> None:
    if not Path.is_dir(path):
        raise FileNotFoundError(f"[_validate_node] Node input/ not found: {path}")
