"""E2E tests for SchedulerExecution and SchedulerJob endpoints.

These cover the full CQRS read/write path against a real SQLite database:
create -> list -> get round-trips for both aggregates. They would have caught
the scheduler_execution/scheduler_job persistence inversion.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import ASGITransport, AsyncClient

from shell.scheduling_service.bootstrap.scheduling.container.scheduling_core_container import (
    SchedulingCoreContainer,
    configure_scheduling_container,
)
from shell.scheduling_service.framework.scheduling.api.app import create_scheduling_app
from shell.scheduling_service.migrations.baseline import run_scheduling_baseline

if TYPE_CHECKING:
    import pathlib


async def _make_app(tmp_path: pathlib.Path):
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'scheduling-e2e.db'}"
    await run_scheduling_baseline(db_url)
    container = SchedulingCoreContainer()
    container.config.db_url.from_value(db_url)
    configure_scheduling_container(container)
    return create_scheduling_app(container)


async def _create_definition(client: AsyncClient) -> str:
    response = await client.post(
        "/api/v1/scheduler-definitions/",
        json={
            "name": "e2e-definition",
            "trigger_config": {
                "source_context": "test",
                "trigger_event_type": "test.event",
            },
            "action_config": {"action_type": "spawn_graph"},
            "execution_policy": {"max_concurrent": 1},
            "enabled": True,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


class TestSchedulerExecutionEndpoints:
    async def test_create_and_get_round_trip(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            definition_id = await _create_definition(client)

            create_resp = await client.post(
                "/api/v1/scheduler-executions/",
                json={"scheduler_definition_id": definition_id},
            )
            assert create_resp.status_code == 201, create_resp.text
            execution_id = create_resp.json()["id"]

            get_resp = await client.get(f"/api/v1/scheduler-executions/{execution_id}")
            assert get_resp.status_code == 200, get_resp.text
            body = get_resp.json()
            assert body["id"] == execution_id
            assert body["scheduler_definition_id"] == definition_id
            assert body["status"] == "PENDING"

    async def test_list_contains_created_execution(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            definition_id = await _create_definition(client)
            create_resp = await client.post(
                "/api/v1/scheduler-executions/",
                json={"scheduler_definition_id": definition_id},
            )
            execution_id = create_resp.json()["id"]

            list_resp = await client.get("/api/v1/scheduler-executions/")
            assert list_resp.status_code == 200, list_resp.text
            ids = [item["id"] for item in list_resp.json()]
            assert execution_id in ids

    async def test_get_missing_returns_404(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/scheduler-executions/nonexistent")
            assert response.status_code == 404


class TestSchedulerJobEndpoints:
    async def test_create_and_get_round_trip(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            definition_id = await _create_definition(client)

            create_resp = await client.post(
                "/api/v1/scheduler-jobs/",
                json={
                    "scheduler_definition_id": definition_id,
                    "name": "e2e-job",
                    "job_type": "messaging",
                    "interval_seconds": 5.0,
                    "batch_size": 10,
                    "enabled": True,
                },
            )
            assert create_resp.status_code == 201, create_resp.text
            job_id = create_resp.json()["id"]

            get_resp = await client.get(f"/api/v1/scheduler-jobs/{job_id}")
            assert get_resp.status_code == 200, get_resp.text
            body = get_resp.json()
            assert body["id"] == job_id
            assert body["scheduler_definition_id"] == definition_id
            assert body["name"] == "e2e-job"
            assert body["job_type"] == "messaging"
            assert body["enabled"] is True

    async def test_list_contains_created_job(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            definition_id = await _create_definition(client)
            create_resp = await client.post(
                "/api/v1/scheduler-jobs/",
                json={
                    "scheduler_definition_id": definition_id,
                    "name": "e2e-job",
                },
            )
            job_id = create_resp.json()["id"]

            list_resp = await client.get("/api/v1/scheduler-jobs/")
            assert list_resp.status_code == 200, list_resp.text
            ids = [item["id"] for item in list_resp.json()]
            assert job_id in ids

    async def test_get_missing_returns_404(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/scheduler-jobs/nonexistent")
            assert response.status_code == 404
