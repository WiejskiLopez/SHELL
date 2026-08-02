"""E2E tests for Session endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import ASGITransport, AsyncClient

from shell.tests.shared.e2e_helpers import TEST_API_KEY, _make_app

if TYPE_CHECKING:
    import pathlib


class TestSessionEndpoints:
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
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post(
                "/api/v1/sessions/",
                headers=headers,
                json={"goal": "filter me"},
            )
            assert create_resp.status_code == 201
            session_id = create_resp.json()["id"]

            resp = await client.get(
                "/api/v1/sessions?user_id=system",
                headers=headers,
            )
            data = resp.json()

        assert resp.status_code == 200
        assert data["total"] == 1
        assert [item["id"] for item in data["items"]] == [session_id]
        assert data["items"][0]["user_id"] == "system"

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
