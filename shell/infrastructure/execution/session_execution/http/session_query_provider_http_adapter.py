from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.session_execution.ports.session_query_provider import (
    SessionQueryProvider,
)
from shell.domain.execution.aggregates.session_execution.value_objects.session_id_ref import (
    SessionIdRef,
)
from shell.domain.execution.aggregates.session_execution.value_objects.session_snapshot import (
    SessionSnapshot,
)
from shell.platform.domain.value_objects.timestamp import Timestamp

if TYPE_CHECKING:
    import httpx


class SessionQueryProviderHttpAdapter(SessionQueryProvider):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def get_by_id(self, session_id: str) -> SessionSnapshot | None:
        response = await self._client.get(f"/api/v1/sessions/{session_id}/history")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()
        return SessionSnapshot(
            session_id=SessionIdRef(data["id"]),
            goal=data["goal"],
            status=data["status"],
            opened_at=_to_timestamp(data["opened_at"]),
            closed_at=_to_timestamp(data["closed_at"]) if data.get("closed_at") else None,
            created_at=_to_timestamp(data.get("created_at", data["opened_at"])),
        )


def _to_timestamp(value: Any) -> Timestamp:
    return Timestamp.from_datetime(datetime.fromisoformat(value))
