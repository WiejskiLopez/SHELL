from __future__ import annotations

import yaml
from collections.abc import Callable
from datetime import datetime

from shell.utils.io.io import default_read_utf8, default_write_utf8
from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE, DIR_TASK


def _init_task_yaml(
    app,
    reader: Callable[[PathType], str] | None = None,
    writer: Callable[[PathType, str], None] | None = None,
) -> None:
    if reader is None:
        reader = default_read_utf8
    if writer is None:
        writer = default_write_utf8

    task_dir = (app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TASK).resolve()
    task_name = app.cli_.cli_properties_.task_name_
    task_yaml_path = task_dir / f"{task_name}.yaml"

    if not Path.is_file(task_yaml_path):
        source_dir = Path.new(app.cli_.cli_properties_.source_dir_)
        source_yaml = source_dir / f"{task_name}.yaml"
        Path.copy_to(source_yaml, task_yaml_path)
        app.app_trace_.record_info('tasker._init_task_yaml._init_task_yaml', f'copy {source_yaml} -> {task_yaml_path}')

    app.runner_.tasker_._task_yaml_file_body = reader(task_yaml_path)
    app.app_trace_.record_info('tasker._init_task_yaml._init_task_yaml', f'read {task_yaml_path}')

    session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    app.runner_.tasker_._session_id = session_id

    data = yaml.safe_load(app.runner_.tasker_._task_yaml_file_body) or {}
    data['session_id'] = session_id
    writer(task_yaml_path, yaml.dump(data, default_flow_style=False, allow_unicode=True))
    app.app_trace_.record_info('tasker._init_task_yaml._init_task_yaml', f'session_id={session_id} written to {task_yaml_path}')
