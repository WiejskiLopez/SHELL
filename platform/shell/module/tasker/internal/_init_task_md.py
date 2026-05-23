from __future__ import annotations

from collections.abc import Callable

from shell.utils.io.io import default_read_utf8
from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE, DIR_TASK


def _init_task_md(
    app,
    reader: Callable[[PathType], str] | None = None,
) -> None:
    if reader is None:
        reader = default_read_utf8

    task_dir = (app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TASK).resolve()
    task_name = app.cli_.cli_properties_.task_name_
    task_md_path = task_dir / f"{task_name}.md"

    if not Path.is_file(task_md_path):
        source_dir = Path.new(app.cli_.cli_properties_.source_dir_)
        source_md = source_dir / f"{task_name}.md"
        Path.copy_to(source_md, task_md_path)
        app.app_trace_.record_info('tasker._init_task_md._init_task_md', f'copy {source_md} -> {task_md_path}')

    app.runner_.tasker_._task_md_file_body = reader(task_md_path)
    app.app_trace_.record_info('tasker._init_task_md._init_task_md', f'read {task_md_path}')
