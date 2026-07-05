from __future__ import annotations

from typing import TYPE_CHECKING

from shell.config.seed.dev_data import seed_dev_data
from shell.infrastructure.platform.persistence.sql import (
    reset_database,
    run_migrations,
    seed_base_data,
)

if TYPE_CHECKING:
    from shell.infrastructure.platform.configuration.shell_config import ShellConfig


async def bootstrap_database(config: ShellConfig) -> None:
    url = config.database_url

    if config.reset_db:
        await reset_database(url)

    await run_migrations(url)
    await seed_base_data(url)

    if config.seed_dev_data:
        await seed_dev_data(url)
