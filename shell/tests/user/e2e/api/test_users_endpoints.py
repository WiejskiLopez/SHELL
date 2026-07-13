"""E2E tests for User endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from httpx import ASGITransport, AsyncClient

from shell.tests.shared.e2e_helpers import TEST_API_KEY, _make_app

if TYPE_CHECKING:
    import pathlib


class TestUserEndpoints:
    async def test_create_user(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/users/", json={"email": "test@example.com"}, headers=headers,
            )
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data

    async def test_get_user_not_found(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with pytest.raises(ValueError):
                await client.get("/api/v1/users/nonexistent", headers=headers)

    async def test_get_user_found(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post(
                "/api/v1/users/", json={"email": "found@example.com"}, headers=headers,
            )
        assert create_resp.status_code == 201
        user_id = create_resp.json()["id"]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/v1/users/{user_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == user_id
        assert data["email"] == "found@example.com"

    async def test_create_then_delete_user(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post(
                "/api/v1/users/", json={"email": "delete_me@example.com"}, headers=headers,
            )
        assert create_resp.status_code == 201
        user_id = create_resp.json()["id"]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            delete_resp = await client.delete(f"/api/v1/users/{user_id}", headers=headers)
        assert delete_resp.status_code == 204

    async def test_update_user(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post(
                "/api/v1/users/", json={"email": "update_me@example.com"}, headers=headers,
            )
        assert create_resp.status_code == 201
        user_id = create_resp.json()["id"]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            update_resp = await client.put(
                f"/api/v1/users/{user_id}",
                json={"email": "updated@example.com"},
                headers=headers,
            )
        assert update_resp.status_code == 204
