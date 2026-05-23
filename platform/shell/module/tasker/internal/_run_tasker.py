from __future__ import annotations

from shell.status.status import Status
from shell.module.tasker.internal._run_iterative_tasker import _run_iterative_tasker


def _run_tasker(tasker) -> Status:
    app = tasker._app
    app.app_trace_.record_info('tasker.Tasker.run_tasker', f"starting task {tasker.task_name_}")
    result = Status.SUCCESS
    try:
        result = _run_iterative_tasker(tasker)
    except Exception as exc:
        result = Status.ERROR
        app.app_trace_.record_error_and_raise('tasker.Tasker.run_tasker', Exception(f"task {tasker.task_name_} failed: {exc}"))
    app.app_trace_.record_info('tasker.Tasker.run_tasker', f"task {tasker.task_name_} completed status={result.name}({int(result)})")
    return result
