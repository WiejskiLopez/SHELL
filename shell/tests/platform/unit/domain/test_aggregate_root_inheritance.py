from __future__ import annotations

from shell.domain.platform.base import Entity
from shell.tests.conftest import _SampleAggregate, _SampleId


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
