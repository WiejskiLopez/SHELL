"""Domain primitives: Entity and AggregateRoot base classes.

These are the foundational building blocks for all domain entities and
aggregate roots. They enforce identity-based equality and (for aggregates)
a recordable stream of domain events that handlers can pull post-commit.

Convention exception:
    Domain entities and aggregates use the ``_field`` + ``@property field``
    pattern (slots-based) instead of dataclass fields. This is documented
    in ``.github/copilot-instructions.md`` and applies ONLY to descendants
    of ``Entity`` / ``AggregateRoot``. Value Objects, Commands, Queries,
    DTOs and Domain Events remain plain ``@dataclass`` instances.
"""
from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from shell_ddd.domain.events.events import DomainEvent

TId = TypeVar("TId")


class Entity(ABC, Generic[TId]):
    """Base class for all domain entities.

    Identity is opaque (``TId``) and immutable after construction.
    Equality and hashing are based exclusively on identity, never on field
    contents. Two entities with the same identity ARE the same entity,
    regardless of their state.
    """

    __slots__ = ("_id",)

    _id: TId

    def __init__(self, id: TId) -> None:
        self._id = id

    @property
    def id(self) -> TId:
        return self._id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        return bool(self._id == other._id)

    def __hash__(self) -> int:
        return hash(self._id)


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
