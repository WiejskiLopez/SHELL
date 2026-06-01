from __future__ import annotations

from shell.utils.path.path import Path


def _move_to_pending(node_stage, filename: str) -> None:
    source = node_stage.stage_active_.active_dir_ / filename
    dest = node_stage.stage_pending_.pending_dir_ / filename
    Path.move(source, dest)
