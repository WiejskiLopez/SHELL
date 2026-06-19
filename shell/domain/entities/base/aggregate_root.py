from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from shell.domain.entities.base.entity import Entity

if TYPE_CHECKING:
    from shell.domain.events.events import DomainEvent

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
        self._events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        events = self._events.copy()
        self._events.clear()
        return events
