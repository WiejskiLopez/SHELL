from __future__ import annotations


def _assert_task_name_set(task_name: str | None, mode: str | None) -> None:
    if mode == 'tasker' and task_name is None:
        raise ValueError("[Cli] --task-name is required in tasker mode")
