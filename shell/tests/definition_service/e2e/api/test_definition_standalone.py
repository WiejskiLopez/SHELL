from __future__ import annotations

from httpx import ASGITransport, AsyncClient
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from shell.definition_service.bootstrap.definition.container.definition_core_container import (
    DefinitionCoreContainer,
)
from shell.definition_service.framework.definition.api.app import create_definition_app
from shell.definition_service.migrations.baseline import run_definition_baseline

TEST_API_KEY = "test-api-key"


async def test_definition_baseline_creates_required_tables(tmp_path) -> None:
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'definition.db'}"
    await run_definition_baseline(db_url)

    engine = create_async_engine(db_url)
    async with engine.connect() as connection:
        tables = await connection.run_sync(
            lambda sync_connection: set(inspect(sync_connection).get_table_names())
        )
    await engine.dispose()

    assert {
        "graph_definition",
        "graph_definition_embedding",
        "node_definition",
        "node_link_definition",
        "runner_config",
        "audit_event",
        "outbox_event",
        "inbox_event",
    } <= tables


async def test_definition_app_health_with_local_container() -> None:
    container = DefinitionCoreContainer()
    container.config.db_url.from_value("sqlite+aiosqlite:///:memory:")
    app = create_definition_app(container, api_key=TEST_API_KEY)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
