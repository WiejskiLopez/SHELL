from __future__ import annotations

from typing import Any, Protocol


class WorkflowSessionProvider(Protocol):
    """Cross-BC port — provides access to workflows associated with a session.

    Implemented by an HTTP adapter in infrastructure/ that calls the execution BC API.
    """

    async def add_session_output(
        self,
        session_id: str,
        user_id: str,
        payload: dict[str, Any],
    ) -> None: ...
