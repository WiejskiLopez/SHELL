from shell.utils.path.path import PathType
from __future__ import annotations


from shell.module.router.router.parse_message_filename import parse_message_filename
from shell.constants.constants import DIR_STAGE_ACTIVE


def _pick_active_file(app, node_stage) -> PathType | None:
    active_dir = node_stage.stage_dir_ / DIR_STAGE_ACTIVE
    app.app_trace_.record_info('router._pick_active_file', f'scanning: {active_dir}')
    active_files = node_stage.get_active_files()
    app.app_trace_.record_info(
        'router._pick_active_file',
        f'active_candidates={len(active_files)}'
    )
    if not active_files:
        return None
    picked = active_files[0]
    app.app_trace_.record_info(
        'router._pick_active_file',
        f'picked: {picked.name}'
    )
    return picked
