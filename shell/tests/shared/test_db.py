"""Helper — resolves test DB path from YAML config, env var, or tmp_path."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest

from shell.platform.infrastructure.configuration.shell_config import ShellConfig


def _resolve_test_db_dir() -> str | None:
    """Return test_db_dir from env var or ShellConfig YAML, or None."""
    env_dir = os.environ.get("SHELL_TEST_DB_DIR")
    if env_dir:
        return env_dir
    try:
        config = ShellConfig.from_environment()
        return config.test_db_dir
    except Exception:
        return None


def test_db_url(
    tmp_path_factory: pytest.TempPathFactory,
    subdir: str = "test",
    db_name: str = "test.db",
) -> str:
    """Return ``sqlite+aiosqlite:///...`` URL for a test database.

    Resolution order (first wins):
    1. ``SHELL_TEST_DB_DIR`` environment variable
    2. ``test_db_dir`` from active YAML config (dev.yaml / prod.yaml)
    3. ``tmp_path_factory`` (pytest temp directory)
    """
    test_db_dir = _resolve_test_db_dir()
    if test_db_dir:
        unique = uuid.uuid4().hex[:8]
        db_path = Path(test_db_dir) / subdir / unique / db_name
        db_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        db_path = tmp_path_factory.mktemp(subdir) / db_name
    return f"sqlite+aiosqlite:///{db_path}"
