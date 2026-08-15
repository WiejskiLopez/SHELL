from __future__ import annotations

from typing import TYPE_CHECKING

from shell.execution.domain.execution.aggregates.session_execution.ports.session_query_provider import (
    SessionQueryProvider,
)
from shell.execution.infrastructure.execution.session_execution.http.contracts.v1.session_response import (
    SessionResponseV1,
)
from shell.execution.infrastructure.execution.session_execution.http.mappers.session_response_to_session_reference import (
    session_response_to_session_reference,
)

if TYPE_CHECKING:
    import httpx

    from shell.execution.domain.execution.aggregates.session_execution.value_objects.session_reference import (
        SessionReference,
    )


class SessionQueryProviderHttpAdapter(SessionQueryProvider):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def get_by_id(self, session_id: str) -> SessionReference | None:
        response = await self._client.get(f"/api/v1/sessions/{session_id}/history")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return session_response_to_session_reference(
            SessionResponseV1.model_validate(response.json())
        )
