from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.messaging.aggregates.message_router.events.message_router_created_event import (
    MessageRouterCreatedEvent,
)
from shell.domain.messaging.aggregates.message_router.value_objects.message_id import MessageId
from shell.domain.platform.base.aggregate_root import AggregateRoot
from shell.domain.platform.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.messaging.aggregates.message_router.value_objects.message_data import (
        MessageData,
    )


class MessageRouter(AggregateRoot[MessageId]):
    __slots__ = (
        "_message_data",
        "_created_at",
    )

    _message_data: MessageData
    _created_at: CreatedAt

    def __init__(
        self,
        *,
        id: MessageId,
        message_data: MessageData,
        created_at: CreatedAt,
    ) -> None:
        super().__init__(id)
        self._message_data = message_data
        self._created_at = created_at

    @classmethod
    def restore(
        cls,
        *,
        id: MessageId,
        message_data: MessageData,
        created_at: CreatedAt,
    ) -> Self:
        return cls(
            id=id,
            message_data=message_data,
            created_at=created_at,
        )

    @property
    def message_data(self) -> MessageData:
        return self._message_data

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @classmethod
    def new(
        cls,
        *,
        id_: MessageId,
        message_data: MessageData | None = None,
        now: datetime,
    ) -> MessageRouter:
        instance = cls(
            id=id_,
            message_data=message_data,
            created_at=CreatedAt.from_datetime(now),
        )
        instance.append_event(
            MessageRouterCreatedEvent.now(
                message_id=instance.id,
                now=CreatedAt.from_datetime(now),
            )
        )
        return instance
