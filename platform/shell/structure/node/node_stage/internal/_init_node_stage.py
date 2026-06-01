from __future__ import annotations
from shell.constants.constants import DOT_NODE, DIR_STAGE


def _init_node_stage(node_stage) -> None:
    node_stage._stage_dir = (node_stage._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_STAGE).resolve()
    node_stage.stage_.init_stage()
