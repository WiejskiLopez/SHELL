from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from shell.execution.bootstrap.execution.container.execution_core_container import (
    ExecutionCoreContainer,
)
from shell.execution.framework.execution.api.app import create_execution_app


async def test_execution_app_health_with_local_container() -> None:
    container = ExecutionCoreContainer()
    container.config.db_url.from_value("sqlite+aiosqlite:///:memory:")
    app = create_execution_app(container, include_routes=True)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    included = [route for route in app.routes if hasattr(route, "original_router")]
    assert len(included) == 6  # 5 aggregate routers + readiness router
