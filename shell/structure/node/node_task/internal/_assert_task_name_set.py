from __future__ import annotations


def _assert_task_name_set(task_name: str | None) -> None:
    if not task_name:
        raise ValueError("[NodeTask] --task-name is required")
