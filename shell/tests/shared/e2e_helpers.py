from __future__ import annotations

from shell.bootstrap.execution.factory.application_factory import ApplicationFactory
from shell.platform.framework.api.app import create_app
from shell.platform.infrastructure.configuration.shell_config import ShellConfig


async def _make_app(tmp_path):
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    core_container = await ApplicationFactory(ShellConfig(database_url=db_url)).build()
    return create_app(core_container)


def _db_url(tmp_path) -> str:
    return f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
