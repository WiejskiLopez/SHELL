from __future__ import annotations

from shell.component.cli.cli.internal._init_cli import _init_cli
from shell.component.cli.cli_properties.cli_properties import CliProperties
from shell.component.config.config.config import Config


class Cli:
    """DOM node for CLI arguments parsed from sys.argv.

    Slots:
        _app            — parent App
        _cli_config     — Config object holding all raw CLI parameter values and defaults
        _cli_properties — CliProperties; typed accessors backed by _cli_config
    """

    __slots__ = (
        "_app",
        "_cli_config",
        "_cli_properties",
    )

    def __init__(self, app=None) -> None:
        self._app = app
        self._cli_config = None
        self._cli_properties = None

    @property
    def cli_config_(self) -> Config:
        if self._cli_config is None:
            self._cli_config = Config()
        return self._cli_config

    @property
    def cli_properties_(self) -> CliProperties:
        if self._cli_properties is None:
            self._cli_properties = CliProperties(self)
        return self._cli_properties

    def init_cli(self, argv=None, runner_root_dir=None, mode: str | None = None) -> None:
        try:
            _init_cli(self, argv=argv, runner_root_dir=runner_root_dir)
        except Exception as exc:
            self._app.app_trace_.record_error_and_raise('cli.Cli.init_cli', exc)
