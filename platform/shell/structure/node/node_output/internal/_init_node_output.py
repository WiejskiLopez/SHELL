from __future__ import annotations
from shell.constants.constants import DOT_NODE, DIR_OUTPUT


def _init_node_output(node_output) -> None:
    node_output._output_dir = Path.resolve(node_output._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_OUTPUT)
