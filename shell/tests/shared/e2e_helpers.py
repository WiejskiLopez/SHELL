from __future__ import annotations

import os
import uuid
from pathlib import Path

from shell.bootstrap.execution.factory.application_factory import ApplicationFactory
from shell.platform.framework.api.app import create_app
from shell.platform.infrastructure.configuration.shell_config import ShellConfig

TEST_API_KEY = "test-api-key"


def _test_db_dir() -> str | None:
    """Resolve test DB directory from env var or YAML config."""
    env_dir = os.environ.get("SHELL_TEST_DB_DIR")
    if env_dir:
        return env_dir
    try:
        config = ShellConfig.from_environment()
        return config.test_db_dir
    except Exception:
        return None


def _resolve_db_path(db_name: str = "test.db") -> str:
    """Return SQLite URL using test db dir (env/YAML), else relative name."""
    test_db_dir = _test_db_dir()
    if test_db_dir:
        db_path = Path(test_db_dir) / "e2e" / uuid.uuid4().hex[:8] / db_name
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{db_path}"
    return db_name


async def _make_app(tmp_path):
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    test_db_dir = _test_db_dir()
    if test_db_dir:
        db_url = _resolve_db_path("test.db")
    config = ShellConfig(database_url=db_url, api_key=TEST_API_KEY)
    core_container = await ApplicationFactory(config).build()
    return create_app(core_container)


def _db_url(tmp_path) -> str:
    test_db_dir = _test_db_dir()
    if test_db_dir:
        return _resolve_db_path("test.db")
    return f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
