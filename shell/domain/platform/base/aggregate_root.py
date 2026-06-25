from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from shell.domain.platform.base.entity import Entity

if TYPE_CHECKING:
    from shell.domain.platform.events import DomainEvent

TId = TypeVar("TId")


class AggregateRoot(Entity[TId]):
    """Base class for aggregate roots.

    Aggregates own a private buffer of domain events recorded by their
    methods. The application layer calls ``pull_events`` after a successful
    transaction to forward them to the event publisher / outbox.
    """

    __slots__ = ("_events",)

    _events: list[DomainEvent]

    def __init__(self, id: TId) -> None:
        super().__init__(id)
        self._events = []

    def append_event(self, event: DomainEvent) -> None:
        object.__setattr__(event, "aggregate_id", self.id.value if hasattr(self.id, "value") else str(self.id))
        object.__setattr__(event, "aggregate_type", type(self).__name__)
        self._events.append(event)
        self._increment_version()

    def pull_events(self) -> list[DomainEvent]:
        events = self._events.copy()
        self._events.clear()
        return events
