from __future__ import annotations


def _clean_node_stage(node_stage) -> None:
    node_stage.stage_active_.clean_stage_active()
    node_stage.stage_pending_.clean_stage_pending()
    node_stage.stage_history_.clean_stage_history()
    node_stage.stage_ignored_.clean_stage_ignored()
    node_stage.stage_dead_.clean_stage_dead()
    node_stage.stage_done_.clean_stage_done()
