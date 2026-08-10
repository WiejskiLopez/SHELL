"""E2E tests for Session endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import ASGITransport, AsyncClient

from shell.tests.shared.e2e_helpers import TEST_API_KEY, _make_app

if TYPE_CHECKING:
    import pathlib


class TestSessionEndpoints:
    async def test_auth_session_login_sets_cookie_and_me_returns_user(
        self, tmp_path: pathlib.Path
    ) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            user_resp = await client.post(
                "/api/v1/users/",
                headers={"X-API-Key": TEST_API_KEY},
                json={"email": "auth-cycle@example.com"},
            )
            assert user_resp.status_code == 201
            user_id = user_resp.json()["id"]

            login_resp = await client.post(
                "/api/v1/auth_session/login",
                json={"email": "auth-cycle@example.com"},
            )
            me_resp = await client.get("/api/v1/auth_session/me")

        assert login_resp.status_code == 200
        assert login_resp.json()["id"]
        assert "shell_session=" in login_resp.headers["set-cookie"]
        assert "httponly" in login_resp.headers["set-cookie"].lower()
        assert me_resp.status_code == 200
        assert me_resp.json() == {"user_id": user_id}

    async def test_auth_session_logout_revokes_cookie_session(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            user_resp = await client.post(
                "/api/v1/users/",
                headers={"X-API-Key": TEST_API_KEY},
                json={"email": "logout-cycle@example.com"},
            )
            assert user_resp.status_code == 201

            login_resp = await client.post(
                "/api/v1/auth_session/login",
                json={"email": "logout-cycle@example.com"},
            )
            assert login_resp.status_code == 200
            assert (await client.get("/api/v1/auth_session/me")).status_code == 200

            logout_resp = await client.post("/api/v1/auth_session/logout")
            me_resp = await client.get("/api/v1/auth_session/me")

        assert logout_resp.status_code == 204
        assert me_resp.status_code == 401

    async def test_auth_session_login_rejects_unknown_email(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth_session/login",
                json={"email": "missing@example.com"},
            )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    async def test_create_session_without_authentication_is_rejected(
        self, tmp_path: pathlib.Path
    ) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/sessions/", json={"goal": "unauthorized"})

        assert resp.status_code == 401

    async def test_system_cannot_create_user_session(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/sessions/",
                headers={"X-API-Key": TEST_API_KEY},
                json={"goal": "system must not own sessions"},
            )

        assert resp.status_code == 403

    async def test_list_sessions_filters_by_user_id(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/sessions?user_id=unknown-user",
                headers=headers,
            )

        assert resp.status_code == 200
        assert resp.json() == {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 100,
            "has_more": False,
        }

    async def test_list_sessions_filters_matching_user(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            user_resp = await client.post(
                "/api/v1/users/",
                headers={"X-API-Key": TEST_API_KEY},
                json={"email": "session-owner@example.com"},
            )
            assert user_resp.status_code == 201
            user_id = user_resp.json()["id"]

            login_resp = await client.post(
                "/api/v1/auth_session/login",
                json={"email": "session-owner@example.com"},
            )
            assert login_resp.status_code == 200

            create_resp = await client.post("/api/v1/sessions/", json={"goal": "filter me"})
            assert create_resp.status_code == 201
            session_id = create_resp.json()["id"]

            resp = await client.get("/api/v1/sessions?user_id=system")
            data = resp.json()

        assert resp.status_code == 200
        assert data["total"] == 1
        assert [item["id"] for item in data["items"]] == [session_id]
        assert data["items"][0]["user_id"] == user_id

    async def test_get_session_history_not_found(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/sessions/nonexistent/history", headers=headers)
        assert resp.status_code == 404

    async def test_get_session_history_response_shape(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/sessions/nonexistent/history", headers=headers)
        assert resp.status_code == 404
