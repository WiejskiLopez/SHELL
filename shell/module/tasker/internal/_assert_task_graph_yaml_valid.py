"""_assert_task_graph_yaml_valid.py
Responsible for one thing: validating the structure of a loaded graph YAML dict.
"""

from __future__ import annotations


def _assert_task_graph_yaml_valid(data: dict) -> None:
    """Raise ValueError when graph YAML is missing required keys or structure."""
    if not isinstance(data, dict):
        raise ValueError(f"Graph YAML must be a mapping, got {type(data).__name__}")
    if 'graph' not in data:
        raise ValueError("Graph YAML is missing required key: 'graph'")
    if not isinstance(data['graph'], list):
        raise ValueError(f"Graph YAML 'graph' must be a list, got {type(data['graph']).__name__}")
    if not data['graph']:
        raise ValueError("Graph YAML 'graph' list must not be empty")
    for i, node in enumerate(data['graph']):
        for required in ('node_name', 'runner_root_dir', 'role', 'type'):
            if required not in node:
                raise ValueError(f"Graph node [{i}] is missing required key: '{required}'")
