from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_OUTPUT


def _has_router_work(non_router_nodes, router_node) -> bool:
    for pn in non_router_nodes:
        output_dir = pn.sub_node_properties_.node_dir_ / DOT_NODE / DIR_OUTPUT
        if Path.exists(output_dir) and any(Path.iterdir(output_dir)):
            return True
    node_stage = router_node.sub_node_properties_.sub_node_node_stage_
    if node_stage.get_active_files():
        return True
    if node_stage.get_pending_files():
        return True
    return False
