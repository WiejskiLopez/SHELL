from __future__ import annotations

from shell.utils.path.path import Path


def _move_to_dead(node_stage, filename: str) -> None:
    source = node_stage.stage_pending_.pending_dir_ / filename
    dest = node_stage.stage_dead_.dead_dir_ / filename
    Path.move(source, dest)
