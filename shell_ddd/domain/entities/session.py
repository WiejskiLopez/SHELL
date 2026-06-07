"""Session + Message — conversation session aggregate."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from shell_ddd.domain.value_objects.ids import MessageId, SessionId, CorrelationId


@dataclass(frozen=True, slots=True)
class Message:
    id: MessageId
    session_id: SessionId
    correlation_id: CorrelationId
    sender: str
    receiver: str
    payload: dict  # type: ignore[type-arg]
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.sender:
            raise ValueError("sender cannot be empty")
        if not self.receiver:
            raise ValueError("receiver cannot be empty")


@dataclass(slots=True)
class Session:
    id: SessionId
    goal: str
    status: str               # "open" | "closed"
    opened_at: datetime
    closed_at: datetime | None
    messages: list[Message] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.goal:
            raise ValueError("goal cannot be empty")
        if self.status not in ("open", "closed"):
            raise ValueError(f"invalid status: {self.status!r}")

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
        payload: dict,  # type: ignore[type-arg]
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
