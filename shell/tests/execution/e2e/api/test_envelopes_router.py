from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import ASGITransport, AsyncClient

from shell.tests.conftest import _make_app

if TYPE_CHECKING:
    import pathlib


class TestEnvelopesRouter:
    async def test_list_envelopes_empty(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/envelopes/workflow/nonexistent-wf")
        assert resp.status_code == 200
        assert resp.json()["envelopes"] == []
