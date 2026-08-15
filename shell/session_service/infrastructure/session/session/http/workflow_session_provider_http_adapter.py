from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.session_service.domain.session.ports.workflow_session_provider import (
    WorkflowSessionProvider,
)

if TYPE_CHECKING:
    import httpx


class WorkflowSessionProviderHttpAdapter(WorkflowSessionProvider):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def add_session_output(
        self,
        session_id: str,
        user_id: str,
        payload: dict[str, Any],
    ) -> None:
        response = await self._client.post(
            "/api/v1/workflows/add-session-output",
            json={
                "session_id": session_id,
                "user_id": user_id,
                "payload": payload,
            },
        )
        response.raise_for_status()
