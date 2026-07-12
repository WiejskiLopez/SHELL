from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MessageGetByIdQuery:
    message_id: str
