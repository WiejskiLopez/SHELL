from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UpdateMessageRouterCommand:
    message_router_id: str

    def __post_init__(self) -> None:
        if not self.message_router_id:
            raise ValueError("message_router_id cannot be empty")
