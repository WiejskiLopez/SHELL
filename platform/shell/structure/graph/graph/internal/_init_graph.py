"""_init_graph.py
Private. Build graph_nodes from DB-backed GraphNodeRecords (no YAML parsing).
"""

from __future__ import annotations

from shell.utils.io.io import default_read_utf8, default_write_utf8
from shell.structure.sub_node.sub_node.sub_node import SubNode
from shell.structure.graph.graph.internal._graph_node_record_to_dict import _graph_node_record_to_dict


def _init_graph(graph, reader=None, writer=None) -> None:
    if reader is None:
        reader = default_read_utf8
    if writer is None:
        writer = default_write_utf8

    app = graph._app
    task_record = app.task_record_
    records = app.task_repo_.get_graph_nodes(task_record.task_id_)

    sub_nodes = []
    for record in records:
        sub_node_dict = _graph_node_record_to_dict(record)
        sub_node = SubNode(app=app)
        sub_node.init_sub_node(sub_node_dict, writer=writer, reader=reader)
        sub_nodes.append(sub_node)
    graph._sub_nodes = sub_nodes

    app.app_trace_.record_info(
        'graph._init_graph._init_graph',
        f'loaded {len(sub_nodes)} sub_nodes from DB task_id={task_record.task_id_} version={task_record.version_}',
    )
