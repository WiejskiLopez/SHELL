from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from datetime import timedelta


class SagaTimeoutRepository(Protocol):
    async def schedule(
        self,
        *,
        saga_id: str,
        saga_key: str,
        step: str,
        due_in: timedelta,
    ) -> None: ...

    async def cancel(self, *, saga_id: str, step: str) -> None: ...
