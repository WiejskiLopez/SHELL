from __future__ import annotations

from pathlib import Path

from shell.platform.infrastructure.persistence.alembic_runner import (
    run_platform_baseline,
    run_versioned_migrations,
)

_MIGRATIONS_DIR = Path(__file__).resolve().parent


async def run_project_baseline(url: str, reset_db: bool = False) -> None:
    await run_platform_baseline(url=url, reset_db=reset_db, include_saga=True)
    await run_versioned_migrations(
        url=url,
        migrations_dir=_MIGRATIONS_DIR,
        service_package="shell.project_service",
        base_class="ProjectSqlAlchemyModelBase",
        reset_db=reset_db,
    )
