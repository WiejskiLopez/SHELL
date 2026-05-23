from __future__ import annotations
from shell.constants.constants import DOT_NODE, DIR_LOGS


def _init_node_logs(node_logs) -> None:
    node_logs._logs_dir = (node_logs._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_LOGS).resolve()
