from shell.utils.path.path import Path, PathType
import sys


from shell.structure.sub_node.sub_node.internal._assert_entrypoint_exists import _assert_entrypoint_exists
from shell.structure.sub_node.sub_node_command.internal._assert_source_dir_set import _assert_source_dir_set
from shell.structure.sub_node.sub_node_command.internal._assert_task_dir_set import _assert_task_dir_set
from shell.structure.sub_node.sub_node_command.internal._assert_task_name_set import _assert_task_name_set
from shell.structure.sub_node.sub_node_command.internal._assert_work_dir_set import _assert_work_dir_set
from shell.structure.sub_node.sub_node_command.internal._assert_model_set import _assert_model_set


def _init_sub_node_command(sub_node_command, sub_node_properties, task_dir, python_exe=None) -> None:
    if python_exe is None:
        python_exe = sys.executable

    app = sub_node_command._app
    node_name = sub_node_properties.sub_node_name_
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

    node_dir = Path.new(parent_node_dir) / node_name
    entrypoint_path = Path.new(runner_root_dir).resolve() / 'entrypoint.py'
    _assert_entrypoint_exists(entrypoint_path)

    sub_node_command.command_.extend_command_args([python_exe, str(entrypoint_path)])
    sub_node_command.command_.extend_command_args(['--node-dir', str(node_dir)])
    sub_node_command.command_.extend_command_args(['--source-dir', str(source_dir)])
    sub_node_command.command_.extend_command_args(['--work-dir', str(work_dir)])
    sub_node_command.command_.extend_command_args(['--task-name', task_name])
    sub_node_command.command_.extend_command_args(['--task-dir', str(task_dir)])

    if parent_node_dir is not None:
        sub_node_command.command_.extend_command_args(['--parent-node-dir', str(parent_node_dir)])
        app.app_trace_.record_info('sub_node_command._init_sub_node_command', f'parent_node_dir set: {parent_node_dir}')
    else:
        app.app_trace_.record_info('sub_node_command._init_sub_node_command', 'parent_node_dir not set')

    if thread_id is not None:
        sub_node_command.command_.extend_command_args(['--parent-thread-id', thread_id])

    if mode == 'agent':
        _assert_model_set(model)
        sub_node_command.command_.extend_command_args(['--model', model])

    role = sub_node_properties.role_
    if role is not None:
        sub_node_command.command_.extend_command_args(['--role', role])

    timeout = sub_node_properties.timeout_
    if timeout is not None:
        sub_node_command.command_.extend_command_args(['--timeout', str(timeout)])

