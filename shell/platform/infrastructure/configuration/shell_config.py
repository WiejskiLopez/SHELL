"""ShellConfig — loads YAML config files with env-var overrides."""

from __future__ import annotations

import contextlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


def _config_dir() -> Path:
    """Resolve the shared environment config directory."""
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


@dataclass
class EventsConfig:
    outbox_batch_size: int = 100
    inbox_batch_size: int = 50
    worker_poll_interval: float = 1.0
    worker_backoff_factor: float = 2.0
    worker_max_backoff: float = 30.0


@dataclass
class ShellConfig:
    """Application configuration loaded from YAML + environment."""

    profile: str = "prod"
    database_url: str = "sqlite+aiosqlite:///shell.db"
    api_key: str = ""
    max_step: int = 20
    max_parallel: int = 4
    log_level: str = "INFO"
    seed_dev_data: bool = False
    reset_db: bool = False
    test_db_dir: str | None = None
    events: EventsConfig = field(default_factory=EventsConfig)

    @classmethod
    def from_environment(cls, component_config_dir: Path | None = None) -> ShellConfig:
        """Build config from YAML files and environment variables.

        Loading order (last wins):
        1. config/default.yaml — shared settings + active_profile
        2. config/{active_profile}.yaml  — profile-specific overrides
        3. Environment variables (SHELL_DATABASE_URL, SHELL_MAX_STEP, SHELL_RESET_DB)

        Safety: reset_db is only honored when active_profile is 'dev'.
        """
        config_dir = _config_dir()

        # 1. Load defaults
        defaults = _load_yaml(config_dir / "default.yaml")

        # 2. Determine active profile from defaults
        active_profile = defaults.get("active_profile", "prod")
        if active_profile not in ("dev", "prod"):
            active_profile = "prod"

        # 3. Load profile-specific config
        profile_file = config_dir / f"{active_profile}.yaml"
        profile_data = _load_yaml(profile_file)

        # 4. Merge shared settings with the component profile, when supplied.
        merged = _deep_merge(defaults, profile_data)
        if component_config_dir is not None:
            component_file = component_config_dir / "database_dev.yaml"
            merged = _deep_merge(merged, _load_yaml(component_file))
        merged["profile"] = active_profile

        # 5. Environment variable overrides (skipped for dev — YAML is the source of truth)
        env_db_url = os.environ.get("SHELL_DATABASE_URL")
        if env_db_url and active_profile != "dev":
            merged["database_url"] = env_db_url

        env_max_step = os.environ.get("SHELL_MAX_STEP")
        if env_max_step is not None:
            with contextlib.suppress(ValueError):
                merged["max_step"] = int(env_max_step)

        # reset_db: only honored in dev profile
        reset_db = False
        if active_profile == "dev":
            env_reset = os.environ.get("SHELL_RESET_DB", "").lower()
            if env_reset in ("1", "true", "yes"):
                reset_db = True

        env_log_level = os.environ.get("SHELL_LOG_LEVEL")
        if env_log_level:
            merged["log_level"] = env_log_level

        env_test_db_dir = os.environ.get("SHELL_TEST_DB_DIR")
        if env_test_db_dir:
            merged["test_db_dir"] = env_test_db_dir

        # Build config object
        return cls(
            profile=merged.get("profile", "prod"),
            database_url=merged.get("database_url", "sqlite+aiosqlite:///shell.db"),
            max_step=int(merged.get("max_step", 20)),
            max_parallel=int(merged.get("max_parallel", 4)),
            log_level=merged.get("log_level", "INFO"),
            seed_dev_data=bool(merged.get("seed_dev_data", False)),
            reset_db=reset_db,
            test_db_dir=merged.get("test_db_dir"),
            events=EventsConfig(
                outbox_batch_size=int(merged.get("events", {}).get("outbox_batch_size", 100)),
                inbox_batch_size=int(merged.get("events", {}).get("inbox_batch_size", 50)),
                worker_poll_interval=float(
                    merged.get("events", {}).get("worker_poll_interval", 1.0)
                ),
                worker_backoff_factor=float(
                    merged.get("events", {}).get("worker_backoff_factor", 2.0)
                ),
                worker_max_backoff=float(merged.get("events", {}).get("worker_max_backoff", 30.0)),
            ),
        )

    def is_dev(self) -> bool:
        return self.profile == "dev"

    def is_prod(self) -> bool:
        return self.profile == "prod"
