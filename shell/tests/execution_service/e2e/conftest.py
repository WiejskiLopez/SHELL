from __future__ import annotations

from shell.execution_service.bootstrap.execution.container.execution_core_container import (
    ExecutionCoreContainer,
    configure_execution_container,
)
from shell.execution_service.framework.execution.api.app import create_execution_app
from shell.execution_service.migrations.baseline import run_execution_baseline

TEST_API_KEY = "test-api-key"


async def make_execution_app(tmp_path):
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'execution-e2e.db'}"
    await run_execution_baseline(db_url)
    container = ExecutionCoreContainer()
    container.config.db_url.from_value(db_url)
    configure_execution_container(container)
    return create_execution_app(container, include_routes=True)
