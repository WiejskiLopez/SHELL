from __future__ import annotations

import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from shell.execution_service.bootstrap.execution.container.execution_core_container import (
    ExecutionCoreContainer,
    configure_execution_container,
)
from shell.execution_service.framework.execution.api.app import create_execution_app
from shell.execution_service.migrations.baseline import run_execution_baseline
from shell.platform.framework.api.principal import Principal, PrincipalKind
from shell.session_service.bootstrap.session.container.session_core_container import (
    SessionCoreContainer,
    configure_session_container,
)
from shell.session_service.framework.session.api.app import create_session_app
from shell.session_service.migrations.baseline import run_session_baseline
from shell.tests.shared.sql_lifecycle import track_session_factory
from shell.tests.shared.test_config import resolve_test_db_dir

if TYPE_CHECKING:
    from fastapi import Request

TEST_API_KEY = "test-api-key"


def _test_db_dir() -> str | None:
    """Resolve the explicit test DB directory from the test environment."""
    return resolve_test_db_dir()


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
    await run_execution_baseline(db_url)
    core_container = ExecutionCoreContainer()
    core_container.config.db_url.from_value(db_url)
    configure_execution_container(core_container)
    track_session_factory(core_container.session_factory())
    return create_execution_app(core_container)


async def _make_session_app(tmp_path):
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'session-test.db'}"
    await run_session_baseline(db_url)
    core_container = SessionCoreContainer()
    core_container.config.db_url.from_value(db_url)
    configure_session_container(core_container)
    track_session_factory(core_container.session_factory())
    app = create_session_app(core_container, api_key=TEST_API_KEY)

    @app.middleware("http")
    async def add_test_principal(request: Request, call_next):
        request.state.principal = Principal("test-user", PrincipalKind.USER)
        return await call_next(request)

    return app


def _db_url(tmp_path) -> str:
    test_db_dir = _test_db_dir()
    if test_db_dir:
        return _resolve_db_path("test.db")
    return f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
