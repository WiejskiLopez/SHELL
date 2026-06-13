"""Unit tests for Entity / AggregateRoot base classes."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from shell_ddd.domain.entities.base import AggregateRoot, Entity
from shell_ddd.domain.events.events import DomainEvent


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
        self.append_event(_SampleEvent(occurred_at=now, payload=payload))


class TestEntityIdentity:
    def test_id_is_exposed_via_property(self) -> None:
        e = _SampleEntity(_SampleId("a"), "x")
        assert e.id == _SampleId("a")

    def test_equality_is_identity_based(self) -> None:
        a1 = _SampleEntity(_SampleId("same"), "label-1")
        a2 = _SampleEntity(_SampleId("same"), "label-2-different")
        assert a1 == a2

    def test_inequality_for_different_ids(self) -> None:
        a = _SampleEntity(_SampleId("a"), "x")
        b = _SampleEntity(_SampleId("b"), "x")
        assert a != b

    def test_hash_matches_identity(self) -> None:
        a1 = _SampleEntity(_SampleId("same"), "label-1")
        a2 = _SampleEntity(_SampleId("same"), "label-2")
        assert hash(a1) == hash(a2)
        assert {a1, a2} == {a1}

    def test_compare_with_non_entity_returns_not_implemented(self) -> None:
        e = _SampleEntity(_SampleId("a"), "x")
        assert (e == "not-an-entity") is False


class TestAggregateEvents:
    def test_pull_events_returns_recorded_events(self) -> None:
        agg = _SampleAggregate(_SampleId("agg-1"), "x")
        agg.do_something("p1")
        agg.do_something("p2")

        events = agg.pull_events()
        assert len(events) == 2
        assert all(isinstance(e, _SampleEvent) for e in events)
        assert [e.payload for e in events] == ["p1", "p2"]  # type: ignore[attr-defined]

    def test_pull_events_clears_buffer(self) -> None:
        agg = _SampleAggregate(_SampleId("agg-2"), "x")
        agg.do_something("once")

        first = agg.pull_events()
        second = agg.pull_events()
        assert len(first) == 1
        assert second == []

    def test_pull_events_returns_copy_not_reference(self) -> None:
        agg = _SampleAggregate(_SampleId("agg-3"), "x")
        agg.do_something("only")

        first = agg.pull_events()
        agg.do_something("after-pull")

        # The first list captured is independent of the aggregate's buffer.
        assert len(first) == 1


class TestAggregateRootInheritance:
    def test_aggregate_is_an_entity(self) -> None:
        agg = _SampleAggregate(_SampleId("agg-x"), "x")
        assert isinstance(agg, Entity)

    def test_aggregate_event_buffer_is_per_instance(self) -> None:
        agg1 = _SampleAggregate(_SampleId("a"), "x")
        agg2 = _SampleAggregate(_SampleId("b"), "y")

        agg1.do_something("only-on-a")

        assert len(agg1.pull_events()) == 1
        assert agg2.pull_events() == []
