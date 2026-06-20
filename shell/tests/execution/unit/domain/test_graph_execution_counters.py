from __future__ import annotations

from shell.domain.execution.aggregates.graph_execution.loop_counter import LoopCounter


class TestLoopCounter:
    def test_is_exhausted_zero_max_never_exhausts(self) -> None:
        lc = LoopCounter("t1", max_loop_count=0)
        lc.increment()
        assert not lc.is_exhausted

    def test_is_exhausted_when_current_reaches_max(self) -> None:
        lc = LoopCounter("t1", max_loop_count=3)
        lc.increment()
        lc.increment()
        assert not lc.is_exhausted
        lc.increment()
        assert lc.is_exhausted

    def test_increment_returns_new_count(self) -> None:
        lc = LoopCounter("t1")
        assert lc.increment() == 1
        assert lc.increment() == 2
