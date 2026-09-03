"""SagaTimeoutRepository — port rejestracji timeoutów kroków sagi."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from datetime import timedelta


class SagaTimeoutRepository(Protocol):
    """Rejestruje oczekiwany timeout kroku; realizowany przez `saga_timeout`."""

    async def schedule(
        self,
        *,
        saga_id: str,
        saga_key: str,
        step: str,
        due_in: timedelta,
    ) -> None: ...

    async def cancel(self, *, saga_id: str, step: str) -> None: ...
