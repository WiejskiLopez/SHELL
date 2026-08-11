from __future__ import annotations

from shell.project.bootstrap.project.container.project_core_container import (
    ProjectCoreContainer,
    configure_project_container,
)
from shell.project.framework.project.project.api.app import create_project_app
from shell.project.migrations.baseline import run_project_baseline

TEST_API_KEY = "test-api-key"


async def make_project_app(tmp_path):
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'project-e2e.db'}"
    await run_project_baseline(db_url)
    container = ProjectCoreContainer()
    container.config.db_url.from_value(db_url)
    configure_project_container(container)
    return create_project_app(container)