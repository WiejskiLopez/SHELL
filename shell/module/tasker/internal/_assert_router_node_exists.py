def _assert_router_node_exists(router_node) -> None:
    if router_node is None:
        raise ValueError(
            "Graph configuration error: no router node (mode='router', role != 'maker') found in graph"
        )
