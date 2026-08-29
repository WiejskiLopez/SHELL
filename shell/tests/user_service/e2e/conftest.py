from __future__ import annotations

from shell.tests.shared.sql_lifecycle import track_session_factory
from shell.user_service.bootstrap.user.container.user_core_container import (
    UserCoreContainer,
    configure_user_container,
)
from shell.user_service.framework.user.api.app import create_user_app
from shell.user_service.migrations.baseline import run_user_baseline

TEST_API_KEY = "test-api-key"


async def make_user_app(tmp_path):
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'user-e2e.db'}"
    await run_user_baseline(db_url)
    container = UserCoreContainer()
    container.config.db_url.from_value(db_url)
    configure_user_container(container)
    track_session_factory(container.session_factory())
    return create_user_app(container, api_key=TEST_API_KEY)
