from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_task_md_exists(path: PathType) -> None:
    if not Path.is_file(path):
        raise FileNotFoundError(f"[NodeTask] task MD not found: {path}")
