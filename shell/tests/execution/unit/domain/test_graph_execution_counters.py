from __future__ import annotations

from shell.domain.execution.aggregates.graph_execution.value_objects.loop_counter import LoopCounter


class TestLoopCounter:
    def test_is_exhausted_zero_max_never_exhausts(self) -> None:
        lc = LoopCounter("t1", max_loop_count=0)
        lc = lc.increment()
        assert not lc.is_exhausted

    def test_is_exhausted_when_current_reaches_max(self) -> None:
        lc = LoopCounter("t1", max_loop_count=3)
        lc = lc.increment()
        lc = lc.increment()
        assert not lc.is_exhausted
        lc = lc.increment()
        assert lc.is_exhausted

    def test_increment_returns_new_instance(self) -> None:
        lc = LoopCounter("t1")
        lc2 = lc.increment()
        assert lc2.current_iteration == 1
        assert lc.current_iteration == 0  # original unchanged
        lc3 = lc2.increment()
        assert lc3.current_iteration == 2
