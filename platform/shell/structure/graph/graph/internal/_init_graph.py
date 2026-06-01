"""_init_graph.py
Private. Load graph YAML from disk, validate and initialize graph_nodes.
"""

from __future__ import annotations

import yaml

from shell.utils.io.io import default_read_utf8, default_write_utf8
from shell.status.status import Status
from shell.structure.sub_node.sub_node.sub_node import SubNode
from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_TASK


def _init_graph(graph, reader=None, writer=None) -> None:
    if reader is None:
        reader = default_read_utf8
    if writer is None:
        writer = default_write_utf8

    task_graph_dict = graph._app.app_node_.node_.node_task_.task_graph_dict_
    task_dir = (graph._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TASK).resolve()

    sub_nodes = []
    for sub_node_dict in task_graph_dict['graph']:
        sub_node = SubNode(app=graph._app)
        sub_node.init_sub_node(sub_node_dict, writer=writer, reader=reader)
        sub_nodes.append(sub_node)
    graph._sub_nodes = sub_nodes

    task_name = graph._app.app_node_.node_.node_task_.task_name_
    yaml_path = task_dir / f'{task_name}.yaml'
    Path.write_text(yaml_path, yaml.dump(task_graph_dict, default_flow_style=False, allow_unicode=True))
    graph._app.app_trace_.record_info(
        'graph._init_graph._init_graph',
        f'persisted graph status to {yaml_path.name}'
    )
