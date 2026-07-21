from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.messaging.aggregates.message_router.events.message_router_created_event import (
    MessageRouterCreatedEvent,
)
from shell.domain.messaging.aggregates.message_router.events.message_router_deleted_event import (
    MessageRouterDeletedEvent,
)
from shell.domain.messaging.aggregates.message_router.events.message_router_updated_event import (
    MessageRouterUpdatedEvent,
)
from shell.domain.messaging.aggregates.message_router.value_objects.message_router_id import (
    MessageRouterId,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.exceptions import DomainError
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.domain.value_objects.updated_at import NONE_UPDATED_AT, UpdatedAt

if TYPE_CHECKING:
    from shell.domain.messaging.aggregates.message_router.value_objects.message_data import (
        MessageData,
    )


class MessageRouter(AggregateRoot[MessageRouterId]):
    __slots__ = (
        "_created_at",
        "_updated_at",
        "_deleted_at",
        "_message_data",
    )

    _message_data: MessageData
    _created_at: CreatedAt
    _updated_at: UpdatedAt

    def __init__(
        self,
        *,
        id: MessageRouterId,
        created_at: CreatedAt,
        updated_at: UpdatedAt = NONE_UPDATED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        message_data: MessageData,
    ) -> None:
        super().__init__(id)
        self._message_data = message_data
        self._created_at = created_at
        self._updated_at = updated_at
        self._deleted_at = deleted_at

    @classmethod
    def restore(
        cls,
        *,
        id: MessageRouterId,
        created_at: CreatedAt,
        updated_at: UpdatedAt = NONE_UPDATED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        message_data: MessageData,
    ) -> Self:
        return cls(
            id=id,
            message_data=message_data,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
        )

    def update(self, now: UpdatedAt) -> None:
        if self._deleted_at.value is not None:
            raise DomainError("Message router already deleted")
        self._updated_at = now
        self.append_event(
            MessageRouterUpdatedEvent.now(
                message_router_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            MessageRouterUpdatedEvent.now(
                message_router_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def delete(self, now: DeletedAt) -> None:
        if self._deleted_at.value is not None:
            raise DomainError("Message router already deleted")
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            MessageRouterDeletedEvent.now(
                message_router_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            MessageRouterDeletedEvent.now(
                message_router_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    @property
    def message_data(self) -> MessageData:
        return self._message_data

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def updated_at(self) -> UpdatedAt:
        return self._updated_at

    @classmethod
    def _new(
        cls,
        *,
        id_: MessageRouterId,
        now: OccurredAt,
        message_data: MessageData,
    ) -> MessageRouter:
        instance = cls(
            id=id_,
            message_data=message_data,
            created_at=CreatedAt.from_datetime(now.value),
        )
        instance.append_event(
            MessageRouterCreatedEvent.now(
                message_router_id=instance.id,
                now=OccurredAt.from_datetime(now.value),
            )
        )
        return instance

    @classmethod
    def new(
        cls,
        *,
        id_: MessageRouterId,
        message_data: MessageData,
        now: CreatedAt,
    ) -> MessageRouter:
        return cls._new(id_=id_, message_data=message_data, now=OccurredAt.from_datetime(now.value))
