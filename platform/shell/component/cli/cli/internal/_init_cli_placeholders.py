def _init_cli_placeholders(cli) -> None:
    cli._app.placeholders_.bind_slots(cli.cli_properties_)
