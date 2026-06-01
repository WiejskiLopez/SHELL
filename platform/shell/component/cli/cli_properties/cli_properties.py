from __future__ import annotations

from shell.utils.path.path import Path, PathType
from datetime import datetime

from shell.component.cli.cli.internal._assert_runner_root_dir_set import _assert_runner_root_dir_set
from shell.component.cli.cli_properties.internal._init_cli_properties import _init_cli_properties


class CliProperties:
    """Typed accessors for CLI parameter values; backed by Cli._cli_config.

    Slots:
        _cli — reference to the owning Cli; set by Cli.cli_properties_
    """

    __slots__ = ("_cli",)

    def __init__(self, cli=None) -> None:
        self._cli = cli

    @property
    def is_version_(self) -> bool:
        return self._cli.cli_config_.config_dict_.get('version') is True

    @property
    def is_help_(self) -> bool:
        return self._cli.cli_config_.config_dict_.get('help') is True

    @property
    def is_clean_(self) -> bool:
        return self._cli.cli_config_.config_dict_.get('clean') is True

    @property
    def is_clean_out_(self) -> bool:
        return self._cli.cli_config_.config_dict_.get('clean_out') is True

    @property
    def is_dry_run_(self) -> bool:
        return self._cli.cli_config_.config_dict_.get('dry_run') is True

    @property
    def is_no_ask_user_(self) -> bool:
        return self._cli.cli_config_.config_dict_.get('no_ask_user') is True

    @property
    def is_autopilot_(self) -> bool:
        return self._cli.cli_config_.config_dict_.get('autopilot') is True

    @property
    def is_allow_all_paths_(self) -> bool:
        return self._cli.cli_config_.config_dict_.get('allow_all_paths') is True

    @property
    def is_allow_all_tools_(self) -> bool:
        return self._cli.cli_config_.config_dict_.get('allow_all_tools') is True

    @property
    def output_format_(self) -> str:
        return self._cli.cli_config_.config_dict_.get('output_format', 'json')

    @property
    def prompt_(self) -> str | None:
        return self._cli.cli_config_.config_dict_.get('prompt')

    @property
    def node_dir_(self) -> str | None:
        return self._cli.cli_config_.config_dict_.get('node_dir')

    @property
    def mode_(self) -> str | None:
        return self._cli.cli_config_.config_dict_.get('mode')

    @property
    def role_(self) -> str | None:
        return self._cli.cli_config_.config_dict_.get('role')

    @property
    def log_level_(self) -> str | None:
        return self._cli.cli_config_.config_dict_.get('log_level')

    @property
    def runner_root_dir_(self) -> PathType:
        value = self._cli.cli_config_.config_dict_.get('runner_root_dir')
        _assert_runner_root_dir_set(value)
        return Path.new(value).parent.resolve()

    @property
    def source_dir_(self) -> PathType | None:
        value = self._cli.cli_config_.config_dict_.get('source_dir')
        if value is None:
            return None
        return Path.new(value).resolve()

    @property
    def task_name_(self) -> str | None:
        return self._cli.cli_config_.config_dict_.get('task_name')

    @property
    def task_id_(self) -> int | None:
        value = self._cli.cli_config_.config_dict_.get('task_id')
        if value is None:
            return None
        return int(value)

    @property
    def task_dir_(self) -> PathType | None:
        value = self._cli.cli_config_.config_dict_.get('task_dir')
        if value is None:
            return None
        return Path.new(value).resolve()

    @property
    def model_(self) -> str | None:
        return self._cli.cli_config_.config_dict_.get('model')

    @property
    def work_dir_(self) -> str | None:
        return self._cli.cli_config_.config_dict_.get('work_dir')

    @property
    def max_step_(self) -> int:
        value = self._cli.cli_config_.config_dict_.get('max_step')
        if value is None:
            return 20
        return value

    @property
    def step_number_(self) -> str:
        return self._cli.cli_config_.config_dict_.get('step_number', '1')

    @property
    def parent_thread_id_(self) -> str | None:
        return self._cli.cli_config_.config_dict_.get('parent_thread_id')

    @property
    def parent_node_dir_(self) -> PathType | None:
        value = self._cli.cli_config_.config_dict_.get('parent_node_dir')
        if value is None:
            return None
        return Path.new(value).resolve()

    @property
    def message_id_(self) -> str:
        return datetime.now().strftime('%Y%m%d%H%M%S%f')

    @property
    def thread_id_(self) -> str:
        if 'thread_id' not in self._cli.cli_config_.config_dict_:
            self._cli.cli_config_.append_config_value('thread_id', datetime.now().strftime('%Y%m%d%H%M%S%f'), 'cli')
        return self._cli.cli_config_.config_dict_['thread_id']

    @property
    def add_dirs_(self) -> list[str]:
        return self._cli.cli_config_.config_dict_.get('add_dirs') or []

    def init_cli_properties(self, args) -> None:
        _init_cli_properties(self, args)
