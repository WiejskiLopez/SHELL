from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from datetime import datetime


class CommandPublisher(Protocol):
    async def publish(
        self,
        command_type: str,
        payload: dict[str, Any],
        occurred_at: datetime,
    ) -> None: ...
