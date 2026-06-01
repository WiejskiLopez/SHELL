"""_assert_node_dir_is_dir.py
Responsible for one thing: raising FileNotFoundError when a node directory does not exist.
"""

from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_node_dir_is_dir(path: PathType, context: str) -> None:
    if not Path.is_dir(path):
        raise FileNotFoundError(f"[{context}] Node directory not found: {path}")
