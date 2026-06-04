from __future__ import annotations

import sys

from shell.utils.path.path import Path
from shell.structure.sub_node.sub_node.internal._assert_entrypoint_exists import _assert_entrypoint_exists
from shell.component.command.command.internal._assert_source_dir_set import _assert_source_dir_set
from shell.component.command.command.internal._assert_task_dir_set import _assert_task_dir_set
from shell.component.command.command.internal._assert_task_name_set import _assert_task_name_set
from shell.component.command.command.internal._assert_work_dir_set import _assert_work_dir_set
from shell.component.command.command.internal._assert_model_set import _assert_model_set


def _init_command_sub_node(command, sub_node_properties, task_dir, app, python_exe=None) -> None:
    if python_exe is None:
        python_exe = sys.executable

    sub_node_name = sub_node_properties.sub_node_name_
    parent_node_dir = sub_node_properties.parent_node_dir_
    runner_root_dir = sub_node_properties.sub_node_runner_root_dir_
    mode = sub_node_properties.mode_
    model = sub_node_properties.model_
    cli = app.cli_
    task_name = sub_node_properties.task_name_ or cli.task_name_
    source_dir = sub_node_properties.source_dir_ or cli.source_dir_
    work_dir = sub_node_properties.work_dir_ or cli.work_dir_
    thread_id = cli.thread_id_

    _assert_source_dir_set(source_dir)
    _assert_work_dir_set(work_dir)
    _assert_task_name_set(task_name)
    _assert_task_dir_set(task_dir)

    node_dir = Path.new(parent_node_dir) / sub_node_name
    entrypoint_path = Path.resolve(Path.new(runner_root_dir)) / 'entrypoint.py'
    _assert_entrypoint_exists(entrypoint_path)

    command.extend_command_args([python_exe, str(entrypoint_path)])
    command.extend_command_args(['--node-dir', str(node_dir)])
    command.extend_command_args(['--source-dir', str(source_dir)])
    command.extend_command_args(['--work-dir', str(work_dir)])
    command.extend_command_args(['--task-name', task_name])
    command.extend_command_args(['--task-dir', str(task_dir)])

    if parent_node_dir is not None:
        command.extend_command_args(['--parent-node-dir', str(parent_node_dir)])
        app.app_trace_.record_info('command._init_command_sub_node', f'parent_node_dir set: {parent_node_dir}')
    else:
        app.app_trace_.record_info('command._init_command_sub_node', 'parent_node_dir not set')

    if thread_id is not None:
        command.extend_command_args(['--parent-thread-id', thread_id])

    if mode == 'agent':
        _assert_model_set(model)
        command.extend_command_args(['--model', model])

    role = sub_node_properties.role_
    if role is not None:
        command.extend_command_args(['--role', role])

    timeout = sub_node_properties.timeout_
    if timeout is not None:
        command.extend_command_args(['--timeout', str(timeout)])
