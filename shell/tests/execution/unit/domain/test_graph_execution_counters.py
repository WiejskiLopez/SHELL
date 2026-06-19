from __future__ import annotations

from shell.domain.execution.aggregates.graph_execution.join_counter import JoinCounter
from shell.domain.execution.aggregates.graph_execution.loop_counter import LoopCounter
from shell.domain.execution.aggregates.graph_execution.parallel_group import ParallelGroup
from shell.domain.platform.value_objects.ids import GraphNodeExecutionId


class TestJoinCounter:
    def test_is_ready_when_current_equals_wait_count(self) -> None:
        jc = JoinCounter("t1", GraphNodeExecutionId("target"), wait_count=2)
        assert not jc.is_ready
        jc.record_completion("a")
        assert not jc.is_ready
        jc.record_completion("b")
        assert jc.is_ready

    def test_duplicate_completion_not_counted(self) -> None:
        jc = JoinCounter("t1", GraphNodeExecutionId("target"), wait_count=1)
        jc.record_completion("a")
        assert jc.is_ready
        jc.record_completion("a")
        assert jc.current_count == 1

    def test_record_completion_returns_ready_status(self) -> None:
        jc = JoinCounter("t1", GraphNodeExecutionId("target"), wait_count=2)
        assert not jc.record_completion("a")
        assert jc.record_completion("b")


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


class TestParallelGroup:
    def test_is_complete_when_all_pending_done(self) -> None:
        pg = ParallelGroup(
            "g1", GraphNodeExecutionId("fork"),
            pending_node_ids={"a", "b"},
        )
        assert not pg.is_complete
        pg.mark_completed("a")
        assert not pg.is_complete
        pg.mark_completed("b")
        assert pg.is_complete

    def test_not_complete_when_no_completed(self) -> None:
        pg = ParallelGroup("g1", GraphNodeExecutionId("fork"))
        assert not pg.is_complete

    def test_mark_completed_removes_from_pending(self) -> None:
        pg = ParallelGroup("g1", GraphNodeExecutionId("fork"), pending_node_ids={"a"})
        pg.mark_completed("a")
        assert "a" not in pg.pending_node_ids
        assert "a" in pg.completed_node_ids
