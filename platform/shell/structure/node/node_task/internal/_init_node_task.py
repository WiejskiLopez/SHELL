from __future__ import annotations


from shell.structure.node.node_task.internal._assert_source_dir_set import _assert_source_dir_set
from shell.structure.node.node_task.internal._assert_task_name_set import _assert_task_name_set
from shell.structure.node.node_task.internal._assert_task_yaml_exists import _assert_task_yaml_exists
from shell.structure.node.node_task.internal._assert_task_md_exists import _assert_task_md_exists
from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE, DIR_TASK


def _init_node_task(node_task) -> None:
    node_dir = Path.new(node_task._app.cli_.cli_properties_.node_dir_).resolve()
    save_dir = node_dir / DOT_NODE / DIR_TASK

    source_dir = node_task._app.cli_.cli_properties_.source_dir_
    _assert_source_dir_set(source_dir)
    task_name = node_task._app.cli_.cli_properties_.task_name_
    _assert_task_name_set(task_name)
    task_yaml_path = source_dir / f'{task_name}.yaml'
    task_md_path = source_dir / f'{task_name}.md'
    _assert_task_yaml_exists(task_yaml_path)
    _assert_task_md_exists(task_md_path)

    node_task._task_name = task_name
    node_task._task_yaml_file_body = Path.read_text(task_yaml_path)
    node_task._task_md_file_body = Path.read_text(task_md_path)

    dest = Path.new(save_dir)
    Path.mkdir(dest)
    Path.write_text(dest / f'{task_name}.yaml', node_task._task_yaml_file_body)
    Path.write_text(dest / f'{task_name}.md', node_task._task_md_file_body)

