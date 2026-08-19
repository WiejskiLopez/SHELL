from __future__ import annotations

import os


def resolve_test_db_dir() -> str | None:
    """Resolve the explicit test database directory from the test environment."""
    return os.environ.get("SHELL_TEST_DB_DIR") or None
