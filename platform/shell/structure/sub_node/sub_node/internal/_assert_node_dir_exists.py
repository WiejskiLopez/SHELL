"""_assert_node_dir_exists.py
Responsible for one thing: raising FileNotFoundError when the node directory is missing.
"""

from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_node_dir_exists(path: PathType) -> None:
    if not Path.is_dir(path):
        raise FileNotFoundError(f"[sub_node] node dir not found: {path}")
