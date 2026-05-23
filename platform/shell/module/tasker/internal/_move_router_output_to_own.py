from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_OUTPUT


def _move_router_output_to_own(tasker, app) -> bool:
    sub_nodes = tasker.graph_.sub_nodes_
    router_nodes = [pn for pn in sub_nodes if pn.mode_ == 'router']
    if not router_nodes:
        return False
    router_output_dir = router_nodes[0].sub_node_properties_.node_dir_ / DOT_NODE / DIR_OUTPUT
    if not Path.exists(router_output_dir):
        return False
    files = [f for f in Path.iterdir(router_output_dir) if Path.is_file(f)]
    if not files:
        return False
    own_output_dir = app.app_node_.node_.node_dir_ / DOT_NODE / DIR_OUTPUT
    Path.mkdir(own_output_dir)
    for file in files:
        Path.move(file, own_output_dir / file.name)
    app.app_trace_.record_info('tasker._run_iterative_tasker', f'moved {len(files)} file(s) from router output to own output')
    return True
