"""app_properties.py
AppProperties — typed accessors for app's config.yaml values.

Slots:
    _app — parent App
"""

from __future__ import annotations

from shell.app.app_properties.internal._assert_app_properties_loaded import _assert_app_properties_loaded


class AppProperties:

    __slots__ = ("_app",)

    def __init__(self, app) -> None:
        self._app = app

    @property
    def name_(self) -> str:
        value = self._app.app_config_.config_dict_.get('name')
        _assert_app_properties_loaded(value)
        return value

    @property
    def mode_(self) -> str | None:
        return self._app.app_config_.config_dict_.get('mode')

    @property
    def role_(self) -> str | None:
        return self._app.app_config_.config_dict_.get('role')

    @property
    def type_(self) -> str | None:
        return self._app.app_config_.config_dict_.get('type')

    @property
    def model_(self) -> str | None:
        return self._app.app_config_.config_dict_.get('model')

    @property
    def command_(self) -> str | None:
        return self._app.app_config_.config_dict_.get('command')

    @property
    def runner_root_dir_(self) -> str | None:
        return self._app.app_config_.config_dict_.get('runner_root_dir')

    @property
    def script_name_(self) -> str | None:
        return self._app.app_config_.config_dict_.get('script_name')

    @property
    def work_dir_(self) -> str | None:
        return self._app.app_config_.config_dict_.get('work_dir')

    @property
    def timeout_(self) -> int | None:
        return self._app.app_config_.config_dict_.get('timeout')

    @property
    def retries_(self) -> int | None:
        return self._app.app_config_.config_dict_.get('retries')

    @property
    def log_level_(self) -> str | None:
        return self._app.app_config_.config_dict_.get('log_level')

    @property
    def max_step_(self) -> int | None:
        return self._app.app_config_.config_dict_.get('max_step')

    @property
    def no_ask_user_(self) -> bool | None:
        return self._app.app_config_.config_dict_.get('no_ask_user')

    @property
    def autopilot_(self) -> bool | None:
        return self._app.app_config_.config_dict_.get('autopilot')
