from __future__ import annotations

from shell.project_service.bootstrap.project.container.project_core_container import (
    ProjectCoreContainer,
    configure_project_container,
)
from shell.project_service.framework.project.project.api.app import create_project_app
from shell.project_service.migrations.baseline import run_project_baseline
from shell.tests.shared.sql_lifecycle import track_session_factory

TEST_API_KEY = "test-api-key"


async def make_project_app(tmp_path):
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'project-e2e.db'}"
    await run_project_baseline(db_url)
    container = ProjectCoreContainer()
    container.config.db_url.from_value(db_url)
    configure_project_container(container)
    track_session_factory(container.session_factory())
    return create_project_app(container)
