from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol


class CommandPublisher(Protocol):
    async def publish(
        self,
        command_type: str,
        payload: dict[str, Any],
        occurred_at: datetime,
    ) -> None: ...
