from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _get_stage_active_files(stage_active) -> list[PathType]:
    from shell.module.router.router.parse_message_filename import parse_message_filename
    active_dir = stage_active.active_dir_
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
