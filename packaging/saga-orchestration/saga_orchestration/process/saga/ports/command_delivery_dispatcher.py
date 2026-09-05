from __future__ import annotations

from typing import Protocol


class Command(Protocol):
    """Structural contract for an operation dispatched by a saga."""


class CommandDeliveryDispatcher(Protocol):
    async def dispatch(self, command: Command, *, target_service: str) -> str: ...
