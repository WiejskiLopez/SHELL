from __future__ import annotations


from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE, DIR_INPUT


def _pick_parent_input(app) -> PathType | None:
    parent_node_dir = app.cli_.cli_properties_.parent_node_dir_
    if parent_node_dir is None:
        return None
    input_dir = parent_node_dir / DOT_NODE / DIR_INPUT
    app.app_trace_.record_info('router._pick_parent_input', f'scanning: {input_dir}')
    if not Path.exists(input_dir):
        return None
    files = sorted([f for f in Path.iterdir(input_dir) if Path.is_file(f)])
    if not files:
        return None
    app.app_trace_.record_info('router._pick_parent_input', f'picked: {files[0].name}')
    return files[0]
