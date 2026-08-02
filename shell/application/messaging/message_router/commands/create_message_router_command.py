from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateMessageRouterCommand:
    message_data: str
    message_context: str

    def __post_init__(self) -> None:
        if not self.message_data:
            raise ValueError("message_data cannot be empty")
        if not self.message_context:
            raise ValueError("message_context cannot be empty")
