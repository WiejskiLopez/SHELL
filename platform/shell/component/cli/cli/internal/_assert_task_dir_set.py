from __future__ import annotations


def _assert_task_dir_set(task_dir: str | None, mode: str | None) -> None:
    if mode == 'router' and task_dir is None:
        raise ValueError("[Cli] --task-dir is required in router mode")
