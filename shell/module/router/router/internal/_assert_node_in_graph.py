"""_assert_node_in_graph.py
Responsible for one thing: raising ValueError when a node id is not found in the graph.
"""


def _assert_node_in_graph(index, node_id: str) -> None:
    """Raise ValueError if index is None (node not found in graph)."""
    if index is None:
        raise ValueError(f"node '{node_id}' not found in graph")
