from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from shell.platform.domain.base import AggregateRoot, Entity
from shell.platform.domain.events import DomainEvent
from shell.platform.domain.value_objects.occurred_at import OccurredAt


def make_sample_event(payload: str = "") -> _SampleEvent:
    now = datetime.now(tz=UTC)
    return _SampleEvent(occurred_at=OccurredAt.from_datetime(now), payload=payload)


@dataclass(frozen=True, slots=True)
class _SampleId:
    value: str


@dataclass(frozen=True, slots=True)
class _SampleEvent(DomainEvent):
    payload: str = ""


class _SampleEntity(Entity[_SampleId]):
    __slots__ = ("_label",)

    def __init__(self, id: _SampleId, label: str) -> None:
        super().__init__(id)
        self._label = label

    @property
    def label(self) -> str:
        return self._label

    def relabel(self, label: str) -> None:
        self._label = label


class _SampleAggregate(AggregateRoot[_SampleId]):
    __slots__ = ("_label",)

    def __init__(self, id: _SampleId, label: str) -> None:
        super().__init__(id)
        self._label = label

    @property
    def label(self) -> str:
        return self._label

    def do_something(self, payload: str) -> None:
        now = datetime.now(tz=UTC)
        self.append_event(_SampleEvent(occurred_at=OccurredAt.from_datetime(now), payload=payload))
