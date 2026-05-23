"""runtime_properties.py
RuntimeProperties — typed accessors for runtime's config.yaml values.

Slots:
    _runtime — parent Runtime
"""

from __future__ import annotations

from shell.component.runtime.runtime_properties.internal._assert_runtime_properties_loaded import _assert_runtime_properties_loaded


class RuntimeProperties:

    __slots__ = ("_runtime",)

    def __init__(self, runtime) -> None:
        self._runtime = runtime

    @property
    def name_(self) -> str:
        value = self._runtime.runtime_config_.config_dict_.get('name')
        _assert_runtime_properties_loaded(value)
        return value

    @property
    def mode_(self) -> str | None:
        return self._runtime.runtime_config_.config_dict_.get('mode')

    @property
    def role_(self) -> str | None:
        return self._runtime.runtime_config_.config_dict_.get('role')

    @property
    def type_(self) -> str | None:
        return self._runtime.runtime_config_.config_dict_.get('type')

    @property
    def model_(self) -> str | None:
        return self._runtime.runtime_config_.config_dict_.get('model')

    @property
    def command_(self) -> str | None:
        return self._runtime.runtime_config_.config_dict_.get('command')

    @property
    def runner_root_dir_(self) -> str | None:
        return self._runtime.runtime_config_.config_dict_.get('runner_root_dir')

    @property
    def script_name_(self) -> str | None:
        return self._runtime.runtime_config_.config_dict_.get('script_name')

    @property
    def work_dir_(self) -> str | None:
        return self._runtime.runtime_config_.config_dict_.get('work_dir')

    @property
    def timeout_(self) -> int | None:
        return self._runtime.runtime_config_.config_dict_.get('timeout')

    @property
    def retries_(self) -> int | None:
        return self._runtime.runtime_config_.config_dict_.get('retries')

    @property
    def log_level_(self) -> str | None:
        return self._runtime.runtime_config_.config_dict_.get('log_level')

    @property
    def max_step_(self) -> int | None:
        return self._runtime.runtime_config_.config_dict_.get('max_step')

    @property
    def no_ask_user_(self) -> bool | None:
        return self._runtime.runtime_config_.config_dict_.get('no_ask_user')

    @property
    def autopilot_(self) -> bool | None:
        return self._runtime.runtime_config_.config_dict_.get('autopilot')
