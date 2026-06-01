from __future__ import annotations

from shell.utils.path.path import PathType

from typing import TYPE_CHECKING

from shell.module.router.router.parse_message_filename import parse_message_filename

if TYPE_CHECKING:
    from shell.structure.node.node_stage.node_stage import NodeStage


def _match_pending(node_stage: 'NodeStage', parsed) -> PathType | None:
    if parsed is None or not parsed.thread_id:
        return None
    for pending_file in node_stage.get_pending_files():
        pending_parsed = parse_message_filename(pending_file.name)
        if pending_parsed is not None and pending_parsed.message_id == parsed.message_id:
            return pending_file
    return None
