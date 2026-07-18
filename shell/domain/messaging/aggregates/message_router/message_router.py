from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.messaging.aggregates.message_router.events.message_router_created_event import (
    MessageRouterCreatedEvent,
)
from shell.domain.messaging.aggregates.message_router.value_objects.message_id import MessageId
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from shell.domain.messaging.aggregates.message_router.value_objects.message_data import (
        MessageData,
    )


class MessageRouter(AggregateRoot[MessageId]):
    __slots__ = (
        "_message_data",
        "_created_at",
        "_updated_at",
    )

    _message_data: MessageData
    _created_at: CreatedAt
    _updated_at: UpdatedAt | None

    def __init__(
        self,
        *,
        id: MessageId,
        message_data: MessageData,
        created_at: CreatedAt | None = None,
        updated_at: UpdatedAt | None = None,
    ) -> None:
        super().__init__(id)
        self._message_data = message_data
        self._created_at = created_at
        self._updated_at = updated_at

    @classmethod
    def restore(
        cls,
        *,
        id: MessageId,
        message_data: MessageData,
        created_at: CreatedAt | None = None,
        updated_at: UpdatedAt | None = None,
    ) -> Self:
        return cls(
            id=id,
            message_data=message_data,
            created_at=created_at,
            updated_at=updated_at,
        )

    def _delete(self) -> None:
        raise NotImplementedError("_delete() not yet implemented")


    def _update(self) -> None:
        raise NotImplementedError("_update() not yet implemented")

    @property
    def message_data(self) -> MessageData:
        return self._message_data

    @property
    def created_at(self) -> CreatedAt | None:
        return self._created_at

    @property
    def updated_at(self) -> UpdatedAt | None:
        return self._updated_at

    @classmethod
    def _new(
        cls,
        *,
        id_: MessageId,
        message_data: MessageData,
        now: CreatedAt,
    ) -> MessageRouter:
        instance = cls(
            id=id_,
            message_data=message_data,
            created_at=now,

        )
        instance.append_event(
            MessageRouterCreatedEvent.now(
                message_id=instance.id,
                now=now,
            )
        )
        return instance

    @classmethod
    def new(
        cls,
        *,
        id_: MessageId,
        message_data: MessageData,
        now: CreatedAt,
    ) -> MessageRouter:
        return cls._new(id_=id_, message_data=message_data, now=now)
