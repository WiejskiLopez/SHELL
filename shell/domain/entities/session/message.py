from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.entities.base.entity import Entity

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.value_objects.ids import CorrelationId, MessageId, SessionId


class Message(Entity[MessageId]):
    __slots__ = ("session_id", "correlation_id", "sender", "receiver", "payload", "created_at")

    def __init__(
        self,
        id: MessageId,
        session_id: SessionId,
        correlation_id: CorrelationId,
        sender: str,
        receiver: str,
        payload: dict,
        created_at: datetime,
    ) -> None:
        if not sender:
            raise ValueError("sender cannot be empty")
        if not receiver:
            raise ValueError("receiver cannot be empty")
        super().__init__(id)
        self.session_id = session_id
        self.correlation_id = correlation_id
        self.sender = sender
        self.receiver = receiver
        self.payload = payload
        self.created_at = created_at
