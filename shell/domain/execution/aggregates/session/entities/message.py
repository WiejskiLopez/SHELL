from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.platform.value_objects.ids import CorrelationId
from shell.domain.execution.aggregates.session.session_id import (
    SessionId,  # noqa: TC002 — SessionId używany w konstruktorze dataclass Message
)
from shell.domain.execution.aggregates.session.value_objects.ids.message_id import (
    MessageId,  # noqa: TC002 — MessageId używany w konstruktorze dataclass Message
)


@dataclass(slots=True)
class Message:
    id: MessageId
    session_id: SessionId
    correlation_id: CorrelationId
    sender: str
    receiver: str
    payload: dict
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.sender:
            raise ValueError("sender cannot be empty")
        if not self.receiver:
            raise ValueError("receiver cannot be empty")
