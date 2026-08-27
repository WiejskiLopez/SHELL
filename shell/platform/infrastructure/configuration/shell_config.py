"""Configuration loader with explicit deployment, runtime and service slices."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from shell.platform.infrastructure.configuration.config_slices import (
        AuthConfig,
        DeploymentConfig,
        PlatformRuntimeConfig,
        ServiceConfig,
    )

_VALID_PROFILES = frozenset({"dev", "prod"})
_VALID_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})


def _config_dir() -> Path:
    """Resolve the shared environment config directory."""
    configured_dir = os.environ.get("SHELL_CONFIG_DIR")
    if configured_dir:
        return Path(configured_dir)
    return Path(__file__).resolve().parents[3] / "config"


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge override into base."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file, returning empty dict if missing."""
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as fh:
        result: Any = yaml.safe_load(fh)
        if result is None:
            raise ValueError(f"Empty or invalid YAML file: {path}")
        if not isinstance(result, dict):
            raise ValueError(f"YAML file {path} does not contain a mapping")
        return result


def _int_setting(values: dict[str, Any], name: str, default: int) -> int:
    raw = values.get(name, default)
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid integer configuration: {name}") from exc
    return value


def _float_setting(values: dict[str, Any], name: str, default: float) -> float:
    raw = values.get(name, default)
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid numeric configuration: {name}") from exc
    return value


def _require_range(name: str, value: int | float, *, minimum: int | float) -> int | float:
    if value < minimum:
        raise ValueError(f"Invalid configuration: {name} must be >= {minimum}")
    return value


@dataclass
class EventsConfig:
    outbox_batch_size: int = 100
    inbox_batch_size: int = 50
    worker_poll_interval: float = 1.0
    worker_backoff_factor: float = 2.0
    worker_max_backoff: float = 30.0
    worker_heartbeat_interval_seconds: float = 15.0
    worker_max_batch_time_seconds: float = 45.0
    broker_url: str = ""


@dataclass(frozen=True, slots=True)
class LoadedConfiguration:
    """Validated configuration result with explicit ownership boundaries."""

    deployment: DeploymentConfig
    platform_runtime: PlatformRuntimeConfig
    auth: AuthConfig
    service: ServiceConfig
    test_db_dir: str | None = None

    @classmethod
    def from_environment(
        cls,
        component_config_dir: Path | None = None,
        *,
        service_name: str | None = None,
    ) -> LoadedConfiguration:
        """Build config from YAML files and environment variables.

        Loading order (last wins):
        1. config/default.yaml — shared settings + active_profile
        2. config/{active_profile}.yaml  — profile-specific overrides
        3. Environment variables (SHELL_DATABASE_URL, SHELL_MAX_STEP, SHELL_RESET_DB)

        Safety: reset_db is only honored when active_profile is 'dev'.
        When service_name is supplied, production requires that service's
        database, broker, and API key environment variables.
        """
        config_dir = (
            component_config_dir
            if component_config_dir is not None and (component_config_dir / "default.yaml").exists()
            else _config_dir()
        )

        # 1. Load defaults
        defaults = _load_yaml(config_dir / "default.yaml")

        # 2. Determine active profile from environment or defaults.
        active_profile = os.environ.get("SHELL_PROFILE", defaults.get("active_profile", "prod"))
        if active_profile not in _VALID_PROFILES:
            raise ValueError(f"Invalid configuration: profile must be one of {_VALID_PROFILES}")

        # 3. Load profile-specific config
        profile_file = config_dir / f"{active_profile}.yaml"
        profile_data = _load_yaml(profile_file)

        # 4. Merge shared settings with the component profile, when supplied.
        merged = _deep_merge(defaults, profile_data)
        if component_config_dir is not None:
            component_file = component_config_dir / "database_dev.yaml"
            merged = _deep_merge(merged, _load_yaml(component_file))
        merged["profile"] = active_profile

        # 5. Environment variable overrides use one precedence for both profiles.
        service_prefix = None if service_name is None else f"{service_name.upper()}_SERVICE"
        database_env = (
            f"{service_prefix}_DATABASE_URL" if service_prefix is not None else "SHELL_DATABASE_URL"
        )
        broker_env = (
            f"{service_prefix}_BROKER_URL"
            if service_prefix is not None
            else "SHELL_EVENTS_BROKER_URL"
        )
        api_key_env = (
            f"{service_prefix}_API_KEY" if service_prefix is not None else "SHELL_API_KEY"
        )

        if database_env in os.environ:
            env_db_url = os.environ[database_env]
            if not env_db_url:
                raise ValueError(f"Invalid configuration: {database_env} must not be empty")
            merged["database_url"] = env_db_url
        elif service_name is not None and active_profile == "prod":
            raise ValueError(f"Invalid production configuration: {database_env} is required")

        env_max_step = os.environ.get("SHELL_MAX_STEP")
        if env_max_step is not None:
            merged["max_step"] = env_max_step

        env_max_parallel = os.environ.get("SHELL_MAX_PARALLEL")
        if env_max_parallel is not None:
            merged["max_parallel"] = env_max_parallel

        # reset_db: only honored in dev profile
        env_reset = os.environ.get("SHELL_RESET_DB", "").lower()
        reset_db = env_reset in ("1", "true", "yes")
        if reset_db and active_profile != "dev":
            raise ValueError("Invalid configuration: reset_db is allowed only in dev profile")

        env_log_level = os.environ.get("SHELL_LOG_LEVEL")
        if env_log_level:
            merged["log_level"] = env_log_level

        if api_key_env in os.environ:
            if service_name is not None and active_profile == "prod" and not os.environ[api_key_env]:
                raise ValueError(f"Invalid production configuration: {api_key_env} must not be empty")
            merged["api_key"] = os.environ[api_key_env]
        elif service_name is not None and active_profile == "prod":
            raise ValueError(f"Invalid production configuration: {api_key_env} is required")

        env_broker_url = os.environ.get(broker_env)
        if env_broker_url:
            merged.setdefault("events", {})["broker_url"] = env_broker_url
        elif service_name is not None and active_profile == "prod":
            raise ValueError(f"Invalid production configuration: {broker_env} is required")

        env_test_db_dir = os.environ.get("SHELL_TEST_DB_DIR")
        if env_test_db_dir:
            merged["test_db_dir"] = env_test_db_dir

        max_step = int(_require_range("max_step", _int_setting(merged, "max_step", 20), minimum=0))
        max_parallel = int(
            _require_range("max_parallel", _int_setting(merged, "max_parallel", 4), minimum=1)
        )
        log_level = str(merged.get("log_level", "INFO")).upper()
        if log_level not in _VALID_LOG_LEVELS:
            raise ValueError(f"Invalid configuration: log_level={log_level}")
        seed_dev_data = bool(merged.get("seed_dev_data", False))
        if seed_dev_data and active_profile != "dev":
            raise ValueError("Invalid configuration: seed_dev_data is allowed only in dev profile")
        events = merged.get("events", {})
        if not isinstance(events, dict):
            raise ValueError("Invalid configuration: events must be a mapping")

        outbox_batch_size = int(
            _require_range(
                "events.outbox_batch_size",
                _int_setting(events, "outbox_batch_size", 100),
                minimum=1,
            )
        )
        inbox_batch_size = int(
            _require_range(
                "events.inbox_batch_size", _int_setting(events, "inbox_batch_size", 50), minimum=1
            )
        )
        worker_poll_interval = float(
            _require_range(
                "events.worker_poll_interval",
                _float_setting(events, "worker_poll_interval", 1.0),
                minimum=0.0,
            )
        )
        worker_backoff_factor = float(
            _require_range(
                "events.worker_backoff_factor",
                _float_setting(events, "worker_backoff_factor", 2.0),
                minimum=0.0,
            )
        )
        worker_max_backoff = float(
            _require_range(
                "events.worker_max_backoff",
                _float_setting(events, "worker_max_backoff", 30.0),
                minimum=0.0,
            )
        )
        worker_heartbeat_interval_seconds = float(
            _require_range(
                "events.worker_heartbeat_interval_seconds",
                _float_setting(events, "worker_heartbeat_interval_seconds", 15.0),
                minimum=0.0,
            )
        )
        worker_max_batch_time_seconds = float(
            _require_range(
                "events.worker_max_batch_time_seconds",
                _float_setting(events, "worker_max_batch_time_seconds", 45.0),
                minimum=0.0,
            )
        )

        from shell.platform.infrastructure.configuration.config_slices import (
            AuthConfig,
            DeploymentConfig,
            PlatformRuntimeConfig,
            ServiceConfig,
        )

        return cls(
            deployment=DeploymentConfig(
                profile=merged.get("profile", "prod"),
                database_url=merged.get("database_url", ""),
            ),
            platform_runtime=PlatformRuntimeConfig(
                log_level=log_level,
                events=EventsConfig(
                    outbox_batch_size=outbox_batch_size,
                    inbox_batch_size=inbox_batch_size,
                    worker_poll_interval=worker_poll_interval,
                    worker_backoff_factor=worker_backoff_factor,
                    worker_max_backoff=worker_max_backoff,
                    worker_heartbeat_interval_seconds=worker_heartbeat_interval_seconds,
                    worker_max_batch_time_seconds=worker_max_batch_time_seconds,
                    broker_url=events.get("broker_url", ""),
                ),
            ),
            auth=AuthConfig(api_key=str(merged.get("api_key", ""))),
            service=ServiceConfig(
                max_step=max_step,
                max_parallel=max_parallel,
                seed_dev_data=seed_dev_data,
                reset_db=reset_db,
            ),
            test_db_dir=merged.get("test_db_dir"),
        )
