from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.platform.aggregates.message.events.message_created_event import (
    MessageCreatedEvent,
)
from shell.domain.platform.aggregates.message.events.message_received_event import (
    MessageReceivedEvent,
)
from shell.domain.platform.aggregates.message.value_objects.business_payload import BusinessPayload
from shell.domain.platform.aggregates.message.value_objects.destination import Destination
from shell.domain.platform.aggregates.message.value_objects.materialized_metadata import (
    MaterializedMetadata,
)
from shell.domain.platform.aggregates.message.value_objects.message_id import MessageId
from shell.domain.platform.aggregates.message.value_objects.message_metadata import MessageMetadata
from shell.domain.platform.aggregates.message.value_objects.message_status import MessageStatus
from shell.domain.platform.aggregates.message.value_objects.message_type import MessageType
from shell.domain.platform.aggregates.message.value_objects.source import Source
from shell.domain.platform.base.aggregate_root import AggregateRoot
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.timestamp import Timestamp

if TYPE_CHECKING:
    from datetime import datetime


class Message(AggregateRoot[MessageId]):
    __slots__ = (
        "_message_type",
        "_business_payload",
        "_metadata",
        "_source",
        "_destination",
        "_status",
        "_materialized_metadata",
        "_created_at",
        "_received_at",
    )

    _message_type: MessageType
    _business_payload: BusinessPayload
    _metadata: MessageMetadata
    _source: Source
    _destination: Destination
    _status: MessageStatus
    _materialized_metadata: MaterializedMetadata
    _created_at: CreatedAt
    _received_at: Timestamp | None

    def __init__(
        self,
        *,
        id: MessageId,
        message_type: MessageType,
        business_payload: BusinessPayload | None = None,
        metadata: MessageMetadata | None = None,
        source: Source,
        destination: Destination,
        status: MessageStatus,
        materialized_metadata: MaterializedMetadata | None = None,
        created_at: CreatedAt | None = None,
        received_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id)
        self._message_type = message_type
        self._business_payload = business_payload or BusinessPayload({})
        self._metadata = metadata or MessageMetadata({})
        self._source = source
        self._destination = destination
        self._status = status
        self._materialized_metadata = materialized_metadata or MaterializedMetadata()
        self._created_at = created_at or CreatedAt.now()
        self._received_at = received_at

    @classmethod
    def restore(
        cls,
        *,
        id: MessageId,
        message_type: MessageType,
        business_payload: BusinessPayload | None = None,
        metadata: MessageMetadata | None = None,
        source: Source,
        destination: Destination,
        status: MessageStatus,
        materialized_metadata: MaterializedMetadata | None = None,
        created_at: CreatedAt | None = None,
        received_at: Timestamp | None = None,
    ) -> Self:
        return cls(
            id=id,
            message_type=message_type,
            business_payload=business_payload,
            metadata=metadata,
            source=source,
            destination=destination,
            status=status,
            materialized_metadata=materialized_metadata,
            created_at=created_at,
            received_at=received_at,
        )

    @property
    def message_type(self) -> MessageType:
        return self._message_type

    @property
    def business_payload(self) -> BusinessPayload:
        return self._business_payload

    @property
    def metadata(self) -> MessageMetadata:
        return self._metadata

    @property
    def source(self) -> Source:
        return self._source

    @property
    def destination(self) -> Destination:
        return self._destination

    @property
    def status(self) -> MessageStatus:
        return self._status

    @property
    def materialized_metadata(self) -> MaterializedMetadata:
        return self._materialized_metadata

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def received_at(self) -> Timestamp | None:
        return self._received_at

    @classmethod
    def new(
        cls,
        *,
        id_: MessageId,
        message_type: str,
        source: str,
        destination: str,
        business_payload: dict[str, object] | None = None,
        metadata: dict[str, object] | None = None,
        materialized_metadata: MaterializedMetadata | None = None,
        now: datetime,
    ) -> Message:
        instance = cls(
            id=id_,
            message_type=MessageType(message_type),
            business_payload=BusinessPayload(business_payload or {}),
            metadata=MessageMetadata(metadata or {}),
            source=Source(source),
            destination=Destination(destination),
            status=MessageStatus.CREATED,
            materialized_metadata=materialized_metadata or MaterializedMetadata(),
            created_at=CreatedAt.from_datetime(now),
        )
        instance.append_event(
            MessageCreatedEvent.now(
                message_id=instance.id,
                message_type=instance._message_type,
                source=instance._source,
                destination=instance._destination,
                now=CreatedAt.from_datetime(now),
            )
        )
        return instance

    def mark_as_received(self, now: datetime) -> None:
        if self._status != MessageStatus.CREATED:
            raise ValueError(
                f"Cannot mark message {self.id.value!r} as received "
                f"from status {self._status.value!r}"
            )
        previous_status = self._status
        self._status = MessageStatus.RECEIVED
        self._received_at = Timestamp.from_datetime(now)
        self.append_event(
            MessageReceivedEvent.now(
                message_id=self.id,
                previous_status=previous_status,
                new_status=self._status,
                now=CreatedAt.from_datetime(now),
            )
        )
