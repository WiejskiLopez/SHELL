def _assert_node_in_graph(index, node_name: str) -> None:
    if index is None:
        raise ValueError(f"node '{node_name}' not found in graph")
