from __future__ import annotations

import pytest

from shell.platform.infrastructure.configuration import shell_config
from shell.platform.infrastructure.configuration.shell_config import ShellConfig


def _write_profile(tmp_path, profile: str) -> None:
    (tmp_path / "default.yaml").write_text(
        f"active_profile: {profile}\nmax_step: 10\nevents:\n  worker_poll_interval: 2.5\n",
        encoding="utf-8",
    )
    (tmp_path / f"{profile}.yaml").write_text(
        "database_url: sqlite+aiosqlite:///profile.db\nmax_parallel: 3\n",
        encoding="utf-8",
    )


def test_shell_config_applies_profile_then_environment_overrides(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_profile(tmp_path, "prod")
    monkeypatch.setattr(shell_config, "_config_dir", lambda: tmp_path)
    monkeypatch.setenv("SHELL_DATABASE_URL", "postgresql+asyncpg://db/test")
    monkeypatch.setenv("SHELL_MAX_STEP", "42")
    monkeypatch.setenv("SHELL_LOG_LEVEL", "DEBUG")

    config = ShellConfig.from_environment()

    assert config.profile == "prod"
    assert config.database_url == "postgresql+asyncpg://db/test"
    assert config.max_step == 42
    assert config.max_parallel == 3
    assert config.log_level == "DEBUG"
    assert config.events.worker_poll_interval == 2.5


def test_reset_database_is_only_enabled_for_dev_profile(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_profile(tmp_path, "prod")
    monkeypatch.setattr(shell_config, "_config_dir", lambda: tmp_path)
    monkeypatch.setenv("SHELL_RESET_DB", "true")

    prod_config = ShellConfig.from_environment()
    assert prod_config.reset_db is False

    _write_profile(tmp_path, "dev")
    dev_config = ShellConfig.from_environment()
    assert dev_config.reset_db is True


def test_invalid_yaml_shape_fails_before_startup(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "default.yaml").write_text("- invalid\n", encoding="utf-8")
    monkeypatch.setattr(shell_config, "_config_dir", lambda: tmp_path)

    with pytest.raises(ValueError, match="does not contain a mapping"):
        ShellConfig.from_environment()
