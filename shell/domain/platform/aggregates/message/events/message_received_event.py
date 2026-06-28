from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

from shell.domain.platform.aggregates.message.value_objects.message_id import MessageId
from shell.domain.platform.aggregates.message.value_objects.message_status import MessageStatus
from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class MessageReceivedEvent(DomainEvent):
    message_id: MessageId
    previous_status: MessageStatus
    new_status: MessageStatus

    @classmethod
    def now(
        cls,
        message_id: MessageId,
        previous_status: MessageStatus,
        new_status: MessageStatus,
        now: datetime,
    ) -> MessageReceivedEvent:
        return cls(
            occurred_at=now,
            message_id=message_id,
            previous_status=previous_status,
            new_status=new_status,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            message_id=MessageId(payload.get("message_id", "")),
            previous_status=MessageStatus(payload.get("previous_status", "created")),
            new_status=MessageStatus(payload.get("new_status", "received")),
        )
