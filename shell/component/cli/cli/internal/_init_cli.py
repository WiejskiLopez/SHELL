from shell.component.cli.cli.internal._parse_args import _parse_args


def _init_cli(cli, argv=None, runner_root_dir=None) -> None:
    config = cli.cli_config_
    config.append_config_value('step_number', '1', 'cli')
    config.append_config_value('allow_all_paths', True, 'cli')
    config.append_config_value('allow_all_tools', True, 'cli')
    config.append_config_value('output_format', 'json', 'cli')
    config.append_config_value('runner_root_dir', runner_root_dir, 'cli')
    args = _parse_args(argv)
    cli.cli_properties_.init_cli_properties(args)
