from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class AppendMessageCommand:
    session_id: str
    correlation_id: str
    sender: str
    receiver: str
    payload: dict[str, object] = field(default_factory=dict)
