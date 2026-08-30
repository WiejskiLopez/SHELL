"""E2E tests for User endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import ASGITransport, AsyncClient

from shell.tests.user_service.e2e.conftest import TEST_API_KEY, make_user_app

if TYPE_CHECKING:
    import pathlib


class TestUserEndpoints:
    async def test_list_users_returns_page(self, tmp_path: pathlib.Path) -> None:
        app = await make_user_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post(
                "/api/v1/users/", json={"email": "alpha@example.com"}, headers=headers
            )
            await client.post("/api/v1/users/", json={"email": "beta@example.com"}, headers=headers)
            resp = await client.get("/api/v1/users", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert body["total"] == 2
        assert body["page"] == 1
        assert body["page_size"] == 100
        assert body["has_more"] is False
        assert len(body["items"]) == 2

    async def test_list_users_pagination(self, tmp_path: pathlib.Path) -> None:
        app = await make_user_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            for i in range(5):
                await client.post(
                    "/api/v1/users/",
                    json={"email": f"user{i}@example.com"},
                    headers=headers,
                )
            resp_page1 = await client.get("/api/v1/users?page=1&page_size=2", headers=headers)
            resp_page3 = await client.get("/api/v1/users?page=3&page_size=2", headers=headers)
        assert resp_page1.status_code == 200
        assert resp_page3.status_code == 200
        p1 = resp_page1.json()
        p3 = resp_page3.json()
        assert len(p1["items"]) == 2
        assert len(p3["items"]) == 1
        assert p1["total"] == 5
        assert p3["total"] == 5
        assert p1["has_more"] is True
        assert p3["has_more"] is False
        assert p1["items"][0]["created_at"] >= p1["items"][1]["created_at"]

    async def test_create_user(self, tmp_path: pathlib.Path) -> None:
        app = await make_user_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/users/",
                json={"email": "test@example.com"},
                headers=headers,
            )
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data

    async def test_get_user_not_found(self, tmp_path: pathlib.Path) -> None:
        app = await make_user_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/users/nonexistent", headers=headers)
        assert resp.status_code == 404

    async def test_get_user_found(self, tmp_path: pathlib.Path) -> None:
        app = await make_user_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post(
                "/api/v1/users/",
                json={"email": "found@example.com"},
                headers=headers,
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
        app = await make_user_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post(
                "/api/v1/users/",
                json={"email": "delete_me@example.com"},
                headers=headers,
            )
        assert create_resp.status_code == 201
        user_id = create_resp.json()["id"]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            delete_resp = await client.delete(f"/api/v1/users/{user_id}", headers=headers)
        assert delete_resp.status_code == 204

    async def test_login_by_email_query(self, tmp_path: pathlib.Path) -> None:
        app = await make_user_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post(
                "/api/v1/users/",
                json={"email": "query@example.com"},
                headers=headers,
            )
            assert create_resp.status_code == 201
            created_id = create_resp.json()["id"]

            resp = await client.get(
                "/api/v1/users/by-email",
                params={"email": "query@example.com"},
                headers=headers,
            )
        assert resp.status_code == 200, f"Got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["id"] == created_id

    async def test_login_by_email_not_found(self, tmp_path: pathlib.Path) -> None:
        app = await make_user_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/users/by-email",
                params={"email": "ghost@example.com"},
                headers=headers,
            )
        assert resp.status_code == 404

    async def test_by_email_requires_authentication(self, tmp_path: pathlib.Path) -> None:
        app = await make_user_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/users/by-email",
                params={"email": "query@example.com"},
            )
        assert resp.status_code == 401

    async def test_change_user(self, tmp_path: pathlib.Path) -> None:
        app = await make_user_app(tmp_path)
        headers = {"X-API-Key": TEST_API_KEY}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post(
                "/api/v1/users/",
                json={"email": "change_me@example.com"},
                headers=headers,
            )
        assert create_resp.status_code == 201
        user_id = create_resp.json()["id"]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            change_resp = await client.put(
                f"/api/v1/users/{user_id}",
                json={"email": "changed@example.com"},
                headers=headers,
            )
        assert change_resp.status_code == 204
