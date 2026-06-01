"""_assert_task_md_exists.py
Responsible for one thing: raising FileNotFoundError when the task markdown file is missing.
"""

from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_task_md_exists(path: PathType) -> None:
    if not Path.is_file(path):
        raise FileNotFoundError(f"[_init_task_md] Task md not found: {path}")
