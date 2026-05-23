from __future__ import annotations

import yaml

from shell.module.tasker.internal._assert_task_graph_yaml_valid import _assert_task_graph_yaml_valid


def _load_graph_yaml(graph) -> dict:
    task_yaml_file_body = graph._app.app_node_.node_.node_task_.task_yaml_file_body_
    graph_yaml = yaml.safe_load(task_yaml_file_body)
    _assert_task_graph_yaml_valid(graph_yaml)
    return graph_yaml
