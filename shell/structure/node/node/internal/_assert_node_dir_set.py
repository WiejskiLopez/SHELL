"""_assert_node_dir_set.py
Responsible for one thing: raising ValueError when node_dir is not set.
"""

from __future__ import annotations


def _assert_node_dir_set(node_dir: str | None) -> None:
    if node_dir is None:
        raise ValueError("[Node] node_dir is not set")
