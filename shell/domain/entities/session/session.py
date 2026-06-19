from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.entities.base.entity import Entity
from shell.domain.entities.session.message import Message

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.value_objects.ids import (
        CorrelationId,
        MessageId,
        SessionId,
    )


class Session(Entity[SessionId]):
    __slots__ = ("goal", "status", "opened_at", "closed_at", "messages")

    def __init__(
        self,
        id: SessionId,
        goal: str,
        status: str,
        opened_at: datetime,
        closed_at: datetime | None,
        messages: list[Message] | None = None,
    ) -> None:
        if not goal:
            raise ValueError("goal cannot be empty")
        if status not in ("open", "closed"):
            raise ValueError(f"invalid status: {status!r}")
        super().__init__(id)
        self.goal = goal
        self.status = status
        self.opened_at = opened_at
        self.closed_at = closed_at
        self.messages = list(messages) if messages is not None else []

    @classmethod
    def open(
        cls,
        id_: SessionId,
        goal: str,
        now: datetime,
    ) -> Session:
        return cls(
            id=id_,
            goal=goal,
            status="open",
            opened_at=now,
            closed_at=None,
        )

    def close(self, now: datetime) -> None:
        if self.status == "closed":
            raise ValueError("Session already closed")
        self.status = "closed"
        self.closed_at = now

    def append_message(
        self,
        msg_id: MessageId,
        correlation_id: CorrelationId,
        sender: str,
        receiver: str,
        payload: dict,
        now: datetime,
    ) -> Message:
        if self.status != "open":
            raise ValueError("Cannot append message to a closed session")
        msg = Message(
            id=msg_id,
            session_id=self.id,
            correlation_id=correlation_id,
            sender=sender,
            receiver=receiver,
            payload=payload,
            created_at=now,
        )
        self.messages.append(msg)
        return msg
