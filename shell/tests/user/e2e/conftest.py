from __future__ import annotations

from shell.user.bootstrap.user.container.user_core_container import (
    UserCoreContainer,
    configure_user_container,
)
from shell.user.framework.user.api.app import create_user_app
from shell.user.migrations.baseline import run_user_baseline

TEST_API_KEY = "test-api-key"


async def make_user_app(tmp_path):
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'user-e2e.db'}"
    await run_user_baseline(db_url)
    container = UserCoreContainer()
    container.config.db_url.from_value(db_url)
    configure_user_container(container)
    return create_user_app(container, api_key=TEST_API_KEY)
