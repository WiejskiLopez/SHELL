from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.session.session.dto.session import SessionDto
from shell.application.session.session.ports.session_query_service import (
    SessionQueryService,
)

if TYPE_CHECKING:
    import httpx


class SessionQueryServiceHttpAdapter(SessionQueryService):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def get_by_id(self, session_id: str) -> SessionDto | None:
        response = await self._client.get(f"/api/v1/sessions/{session_id}/history")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()
        return SessionDto(
            id=data["id"],
            goal=data["goal"],
            status=data["status"],
            opened_at=data["opened_at"],
            closed_at=data.get("closed_at"),
            created_at=data.get("created_at", data["opened_at"]),
        )
