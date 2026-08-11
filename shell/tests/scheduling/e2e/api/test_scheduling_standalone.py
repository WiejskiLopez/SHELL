from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from shell.scheduling.bootstrap.scheduling.container.scheduling_core_container import (
    SchedulingCoreContainer,
    configure_scheduling_container,
)
from shell.scheduling.framework.scheduling.api.app import create_scheduling_app


async def test_scheduling_app_health_with_local_container() -> None:
    container = SchedulingCoreContainer()
    container.config.db_url.from_value("sqlite+aiosqlite:///:memory:")
    configure_scheduling_container(container)
    app = create_scheduling_app(container)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
