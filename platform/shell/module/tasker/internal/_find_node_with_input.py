from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_INPUT


def _find_node_with_input(non_router_nodes) -> object | None:
    for pn in non_router_nodes:
        input_dir = pn.sub_node_properties_.node_dir_ / DOT_NODE / DIR_INPUT
        if Path.exists(input_dir) and any(Path.iterdir(input_dir)):
            return pn
    return None
