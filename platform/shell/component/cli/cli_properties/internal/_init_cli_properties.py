from shell.component.cli.cli.internal._assert_node_dir_set import _assert_node_dir_set
from shell.component.cli.cli.internal._assert_source_dir_set import _assert_source_dir_set
from shell.component.cli.cli.internal._assert_task_name_set import _assert_task_name_set
from shell.component.cli.cli.internal._assert_task_dir_set import _assert_task_dir_set
from shell.component.cli.cli.internal._assert_model_set import _assert_model_set
from shell.component.cli.cli.internal._assert_work_dir_set import _assert_work_dir_set


def _init_cli_properties(cli_properties, args) -> None:
    config = cli_properties._cli.cli_config_
    if args.add_dirs:
        config.append_config_value('add_dirs', args.add_dirs, 'cli')
    if args.node_dir is not None:
        config.append_config_value('node_dir', args.node_dir, 'cli')
    if args.mode is not None:
        config.append_config_value('mode', args.mode, 'cli')
    if args.role is not None:
        config.append_config_value('role', args.role, 'cli')
    if args.type is not None:
        config.append_config_value('type', args.type, 'cli')
    if args.version:
        config.append_config_value('version', True, 'cli')
    if args.help:
        config.append_config_value('help', True, 'cli')
    if args.clean:
        config.append_config_value('clean', True, 'cli')
    if args.clean_out:
        config.append_config_value('clean_out', True, 'cli')
    if args.dry_run:
        config.append_config_value('dry_run', True, 'cli')
    if args.log_level is not None:
        config.append_config_value('log_level', args.log_level, 'cli')
    if args.no_ask_user:
        config.append_config_value('no_ask_user', True, 'cli')
    if args.autopilot:
        config.append_config_value('autopilot', True, 'cli')
    if args.prompt is not None:
        config.append_config_value('prompt', args.prompt, 'cli')
    if args.prompt_dir is not None:
        config.append_config_value('prompt_dir', args.prompt_dir, 'cli')
    if args.timeout is not None:
        config.append_config_value('timeout', args.timeout, 'cli')
    if args.source_dir is not None:
        config.append_config_value('source_dir', args.source_dir, 'cli')
    if args.task_name is not None:
        config.append_config_value('task_name', args.task_name, 'cli')
    if args.task_dir is not None:
        config.append_config_value('task_dir', args.task_dir, 'cli')
    if args.model is not None:
        config.append_config_value('model', args.model, 'cli')
    config.append_config_value('work_dir', args.work_dir, 'cli')
    if args.max_step is not None:
        config.append_config_value('max_step', args.max_step, 'cli')
    if args.parent_thread_id is not None:
        config.append_config_value('parent_thread_id', args.parent_thread_id, 'cli')
    if args.parent_node_dir is not None:
        config.append_config_value('parent_node_dir', args.parent_node_dir, 'cli')
    d = config.config_dict_
    _assert_node_dir_set(d.get('node_dir'), d.get('mode'))
    _assert_source_dir_set(d.get('source_dir'), d.get('mode'))
    _assert_task_name_set(d.get('task_name'), d.get('mode'))
    _assert_task_dir_set(d.get('task_dir'), d.get('mode'))
    _assert_model_set(d.get('model'), d.get('mode'))
    _assert_work_dir_set(d.get('work_dir'))
