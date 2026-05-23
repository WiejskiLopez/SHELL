from shell.component.cli.cli.internal._parse_args import _parse_args


def _init_cli(cli, argv=None) -> None:
    args = _parse_args(argv)
    cli.cli_properties_.init_cli_properties(args)
