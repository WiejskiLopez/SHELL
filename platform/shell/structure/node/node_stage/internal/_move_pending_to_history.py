from __future__ import annotations

from shell.utils.path.path import Path


def _move_pending_to_history(node_stage, filename: str) -> None:
    source = node_stage.stage_pending_.pending_dir_ / filename
    dest = node_stage.stage_history_.history_dir_ / filename
    Path.move(source, dest)
