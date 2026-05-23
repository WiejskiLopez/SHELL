from __future__ import annotations


from shell.module.router.router.parse_message_filename import parse_message_filename
from shell.utils.path.path import Path, PathType
from shell.constants.constants import DIR_STAGE_ACTIVE


def _get_active_files(node_stage) -> list[PathType]:
    active_dir = node_stage._stage_dir / DIR_STAGE_ACTIVE
    if not Path.exists(active_dir):
        return []
    candidates = [f for f in Path.iterdir(active_dir) if Path.is_file(f)]

    def _msg_id_key(f: PathType) -> int:
        parsed = parse_message_filename(f.name)
        if parsed is None:
            return -1
        try:
            return int(parsed.sequence_id)
        except ValueError:
            return -1

    return sorted(candidates, key=_msg_id_key)
