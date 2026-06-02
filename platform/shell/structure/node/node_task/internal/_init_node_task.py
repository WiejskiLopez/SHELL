from __future__ import annotations


def _init_node_task(node_task) -> None:
    app = node_task._app
    task_name = app.cli_.cli_properties_.task_name_
    if not task_name:
        return
    record = app.task_repo_.get_current_task(task_name)
    if record is None:
        return
    node_task._task_name = record.name_
    node_task._task_yaml_file_body = record.body_yaml_raw_
    node_task._task_md_file_body = record.body_md_

