def _assert_graph_node_role_set(role: str | None, node_name: str) -> None:
    if not role:
        raise ValueError(f"[Router] graph node '{node_name}' has no role defined")
