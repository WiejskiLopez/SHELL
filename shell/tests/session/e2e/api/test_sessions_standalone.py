from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from shell.tests.session.e2e.conftest import TEST_USER_ID, make_session_app


async def test_session_standalone_create_and_list(tmp_path) -> None:
    app = await make_session_app(tmp_path)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        create_response = await client.post("/api/v1/sessions/", json={"goal": "standalone"})
        assert create_response.status_code == 201
        session_id = create_response.json()["id"]

        get_response = await client.get(f"/api/v1/sessions/{session_id}")
        assert get_response.status_code == 200
        assert get_response.json()["user_id"] == TEST_USER_ID

        list_response = await client.get("/api/v1/sessions")
        assert list_response.status_code == 200
        assert list_response.json()["total"] == 1