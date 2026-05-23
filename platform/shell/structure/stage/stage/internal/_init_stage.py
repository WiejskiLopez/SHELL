from __future__ import annotations


def _init_stage(stage) -> None:
    stage.stage_active_.init_stage_active()
    stage.stage_pending_.init_stage_pending()
    stage.stage_history_.init_stage_history()
    stage.stage_ignored_.init_stage_ignored()
    stage.stage_dead_.init_stage_dead()
    stage.stage_done_.init_stage_done()
