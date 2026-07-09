from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetMessageByIdQuery:
    message_id: str
