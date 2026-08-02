from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.domain.base.entity import Entity, TId

if TYPE_CHECKING:
    from shell.platform.domain.events import DomainEvent
    from shell.platform.domain.messages import DomainMessage


class AggregateRoot(Entity[TId]):
    """Base class for aggregate roots.

    Aggregates own a private buffer of domain events recorded by their
    methods. The application layer calls ``pull_events`` after a successful
    transaction to forward them to the event publisher / outbox.
    """

    __slots__ = ("_events", "_messages")

    _events: list[DomainEvent]
    _messages: list[DomainMessage]

    def __init__(self, id: TId) -> None:
        super().__init__(id)
        self._events = []
        self._messages = []

    def append_event(self, event: DomainEvent) -> None:
        from shell.platform.domain.value_objects.aggregate_id import AggregateId
        from shell.platform.domain.value_objects.aggregate_name import AggregateName

        object.__setattr__(
            event,
            "aggregate_id",
            AggregateId(self.id.value if hasattr(self.id, "value") else str(self.id)),
        )
        object.__setattr__(event, "aggregate_name", AggregateName(type(self).__name__))
        self._events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        events = self._events.copy()
        self._events.clear()
        return events

    def append_message(self, message: DomainMessage) -> None:
        from shell.platform.domain.value_objects.aggregate_id import AggregateId
        from shell.platform.domain.value_objects.aggregate_name import AggregateName

        object.__setattr__(
            message,
            "aggregate_id",
            AggregateId(self.id.value if hasattr(self.id, "value") else str(self.id)),
        )
        object.__setattr__(message, "aggregate_name", AggregateName(type(self).__name__))
        self._messages.append(message)

    def pull_messages(self) -> list[DomainMessage]:
        messages = self._messages.copy()
        self._messages.clear()
        return messages
