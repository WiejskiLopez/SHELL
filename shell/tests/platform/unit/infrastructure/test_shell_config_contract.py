from __future__ import annotations

import pytest

from shell.platform.infrastructure.configuration import shell_config
from shell.platform.infrastructure.configuration.shell_config import LoadedConfiguration


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
    monkeypatch.setenv("SHELL_API_KEY", "test-api-key")

    config = LoadedConfiguration.from_environment()

    assert config.deployment.profile == "prod"
    assert config.deployment.database_url == "postgresql+asyncpg://db/test"
    assert config.service.max_step == 42
    assert config.service.max_parallel == 3
    assert config.platform_runtime.log_level == "DEBUG"
    assert config.auth.api_key == "test-api-key"
    assert config.platform_runtime.events.worker_poll_interval == 2.5


def test_reset_database_is_only_enabled_for_dev_profile(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_profile(tmp_path, "prod")
    monkeypatch.setattr(shell_config, "_config_dir", lambda: tmp_path)
    monkeypatch.setenv("SHELL_RESET_DB", "true")

    with pytest.raises(ValueError, match="reset_db"):
        LoadedConfiguration.from_environment()

    _write_profile(tmp_path, "dev")
    dev_config = LoadedConfiguration.from_environment()
    assert dev_config.service.reset_db is True


def test_profile_environment_override_is_explicit(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_profile(tmp_path, "prod")
    monkeypatch.setattr(shell_config, "_config_dir", lambda: tmp_path)
    monkeypatch.setenv("SHELL_PROFILE", "dev")

    config = LoadedConfiguration.from_environment()

    assert config.deployment.profile == "dev"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("SHELL_MAX_STEP", "not-an-int", "max_step"),
        ("SHELL_MAX_PARALLEL", "0", "max_parallel"),
        ("SHELL_LOG_LEVEL", "TRACE", "log_level"),
    ],
)
def test_invalid_environment_values_fail_fast(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: str,
    message: str,
) -> None:
    _write_profile(tmp_path, "prod")
    monkeypatch.setattr(shell_config, "_config_dir", lambda: tmp_path)
    monkeypatch.setenv(field, value)

    with pytest.raises(ValueError, match=message):
        LoadedConfiguration.from_environment()


def test_seed_dev_data_is_rejected_in_prod(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_profile(tmp_path, "prod")
    (tmp_path / "prod.yaml").write_text("seed_dev_data: true\n", encoding="utf-8")
    monkeypatch.setattr(shell_config, "_config_dir", lambda: tmp_path)

    with pytest.raises(ValueError, match="seed_dev_data"):
        LoadedConfiguration.from_environment()


def test_shell_config_exposes_explicit_ownership_slices(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_profile(tmp_path, "prod")
    monkeypatch.setattr(shell_config, "_config_dir", lambda: tmp_path)
    monkeypatch.setenv("SHELL_API_KEY", "secret")

    config = LoadedConfiguration.from_environment()

    assert config.deployment.database_url == config.deployment.database_url
    assert config.platform_runtime.log_level == config.platform_runtime.log_level
    assert config.auth.api_key == "secret"
    assert config.service.max_parallel == config.service.max_parallel


def test_invalid_yaml_shape_fails_before_startup(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "default.yaml").write_text("- invalid\n", encoding="utf-8")
    monkeypatch.setattr(shell_config, "_config_dir", lambda: tmp_path)

    with pytest.raises(ValueError, match="does not contain a mapping"):
        LoadedConfiguration.from_environment()


@pytest.mark.parametrize(
    "missing_variable",
    [
        "DEFINITION_SERVICE_DATABASE_URL",
        "DEFINITION_SERVICE_BROKER_URL",
        "DEFINITION_SERVICE_API_KEY",
    ],
)
def test_production_service_configuration_requires_owned_values(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    missing_variable: str,
) -> None:
    _write_profile(tmp_path, "prod")
    monkeypatch.setattr(shell_config, "_config_dir", lambda: tmp_path)
    for variable in (
        "DEFINITION_SERVICE_DATABASE_URL",
        "DEFINITION_SERVICE_BROKER_URL",
        "DEFINITION_SERVICE_API_KEY",
    ):
        monkeypatch.setenv(variable, "configured")
    monkeypatch.delenv(missing_variable)

    with pytest.raises(ValueError, match=missing_variable):
        LoadedConfiguration.from_environment(service_name="definition")


def test_production_service_configuration_uses_owned_values(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_profile(tmp_path, "prod")
    monkeypatch.setattr(shell_config, "_config_dir", lambda: tmp_path)
    monkeypatch.setenv("DEFINITION_SERVICE_DATABASE_URL", "postgresql+asyncpg://definition/db")
    monkeypatch.setenv("DEFINITION_SERVICE_BROKER_URL", "amqp://definition")
    monkeypatch.setenv("DEFINITION_SERVICE_API_KEY", "definition-key")
    monkeypatch.setenv("SHELL_DATABASE_URL", "postgresql+asyncpg://shared/db")
    monkeypatch.setenv("SHELL_EVENTS_BROKER_URL", "amqp://shared")
    monkeypatch.setenv("SHELL_API_KEY", "shared-key")

    config = LoadedConfiguration.from_environment(service_name="definition")

    assert config.deployment.database_url == "postgresql+asyncpg://definition/db"
    assert config.platform_runtime.events.broker_url == "amqp://definition"
    assert config.auth.api_key == "definition-key"


def test_production_service_configuration_rejects_empty_owned_api_key(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_profile(tmp_path, "prod")
    monkeypatch.setattr(shell_config, "_config_dir", lambda: tmp_path)
    monkeypatch.setenv("DEFINITION_SERVICE_DATABASE_URL", "postgresql+asyncpg://definition/db")
    monkeypatch.setenv("DEFINITION_SERVICE_BROKER_URL", "amqp://definition")
    monkeypatch.setenv("DEFINITION_SERVICE_API_KEY", "")

    with pytest.raises(ValueError, match="DEFINITION_SERVICE_API_KEY"):
        LoadedConfiguration.from_environment(service_name="definition")
