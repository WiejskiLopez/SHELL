from __future__ import annotations

from shell.tests.conftest import _SampleAggregate, _SampleEvent, _SampleId


class TestAggregateEvents:
    def test_pull_events_returns_recorded_events(self) -> None:
        agg = _SampleAggregate(_SampleId("agg-1"), "x")
        agg.do_something("p1")
        agg.do_something("p2")

        events = agg.pull_events()
        assert len(events) == 2
        payloads = []
        for e in events:
            assert isinstance(e, _SampleEvent)
            payloads.append(e.payload)
        assert payloads == ["p1", "p2"]

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

        assert len(first) == 1
