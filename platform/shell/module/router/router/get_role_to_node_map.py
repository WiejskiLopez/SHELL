def get_role_to_node_map(graph: list) -> dict[str, dict]:
    """Return mapping of role -> node for all nodes that have a role defined."""
    return {n['role']: n for n in graph if n.get('role')}
