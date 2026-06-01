from __future__ import annotations

from shell.module.router.router_base.internal._assert_task_yaml_file_body_set import _assert_task_yaml_file_body_set
from shell.module.router.router_base.internal._assert_task_yaml_in_task_dir import _assert_task_yaml_in_task_dir
from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_TASK


def _init_router_base(router_base, reader=None) -> None:
    task_dir = (router_base._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TASK).resolve()
    yaml_files = Path.glob(task_dir, '*.yaml')
    _assert_task_yaml_in_task_dir(yaml_files, task_dir)
    task_yaml_file_body = Path.read_text(yaml_files[0])
    _assert_task_yaml_file_body_set(task_yaml_file_body)
    router_base._app.app_node_.node_.node_task_._task_yaml_file_body = task_yaml_file_body
    router_base._app.app_node_.node_.node_task_._task_name = yaml_files[0].stem
    router_base.graph_.init_graph()
