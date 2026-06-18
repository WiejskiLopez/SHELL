from __future__ import annotations

from typing import TYPE_CHECKING

from shell.bootstrap.factory.application_factory import ApplicationFactory

if TYPE_CHECKING:
    import pathlib


async def _make_app(tmp_path: pathlib.Path):
    from shell.framework.api.app import create_app

    db_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    core_container = await ApplicationFactory(database_url=db_url).build()
    return create_app(core_container)
