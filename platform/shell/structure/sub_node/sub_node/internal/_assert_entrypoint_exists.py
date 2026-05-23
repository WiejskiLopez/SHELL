"""_assert_entrypoint_exists.py
Responsible for one thing: raising FileNotFoundError when entrypoint.py is missing.
"""

from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_entrypoint_exists(path: PathType) -> None:
    if not Path.is_file(path):
        raise FileNotFoundError(f"[SubNode] entrypoint not found: {path}")
