from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import ASGITransport, AsyncClient
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from shell.tests.shared.sql_lifecycle import track_session_factory
from shell.user_service.bootstrap.user.container.user_core_container import (
    UserCoreContainer,
    configure_user_container,
)
from shell.user_service.framework.user.api.app import create_user_app
from shell.user_service.infrastructure.user.auth_session.persistence.sql.models.auth_session import (
    AuthSessionModel,  # noqa: F401 -- register SQLAlchemy model metadata
)
from shell.user_service.infrastructure.user.user.persistence.sql.models.user import (  # noqa: F401 -- register SQLAlchemy model metadata
    UserModel,
)
from shell.user_service.migrations.baseline import run_user_baseline

if TYPE_CHECKING:
    import pathlib


async def test_user_app_builds_with_user_core_container() -> None:
    container = UserCoreContainer()
    container.config.db_url.from_value("sqlite+aiosqlite:///:memory:")
    configure_user_container(container)
    track_session_factory(container.session_factory())
    app = create_user_app(container, api_key="test-key")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    included_routers = [route for route in app.routes if hasattr(route, "original_router")]
    assert any(
        any(getattr(child, "path", None) == "/users" for child in route.original_router.routes)
        for route in included_routers
    )


async def test_user_app_auth_session_flow(tmp_path: pathlib.Path) -> None:
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'user.db'}"
    await run_user_baseline(db_url)

    container = UserCoreContainer()
    container.config.db_url.from_value(db_url)
    configure_user_container(container)
    track_session_factory(container.session_factory())
    app = create_user_app(container, api_key="test-key")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = {"X-API-Key": "test-key"}
        create_response = await client.post(
            "/api/v1/users/",
            json={"email": "auth@example.com"},
            headers=headers,
        )
        assert create_response.status_code == 201

        login_response = await client.post(
            "/api/v1/auth_session/login",
            json={"email": "auth@example.com"},
        )
        assert login_response.status_code == 200

        me_response = await client.get("/api/v1/auth_session/me")
        assert me_response.status_code == 200
        assert me_response.json()["user_id"] == create_response.json()["id"]

        user_response = await client.get(f"/api/v1/users/{create_response.json()['id']}")
        assert user_response.status_code == 200

        logout_response = await client.post("/api/v1/auth_session/logout")
        assert logout_response.status_code == 204

        expired_me_response = await client.get("/api/v1/auth_session/me")
        assert expired_me_response.status_code == 401


async def test_user_baseline_creates_required_tables(tmp_path: pathlib.Path) -> None:
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'fresh-user.db'}"

    await run_user_baseline(db_url)

    engine = create_async_engine(db_url)
    async with engine.connect() as connection:
        tables = await connection.run_sync(
            lambda sync_connection: set(inspect(sync_connection).get_table_names())
        )
    await engine.dispose()

    assert tables == {
        "alembic_version",
        "user",
        "auth_sessions",
        "user_skill",
        "user_state",
        "audit_event",
        "outbox_event",
        "inbox_event",
        "outbox_command",
        "inbox_command",
        "processed_delivery",
        "worker_heartbeat",
    }
