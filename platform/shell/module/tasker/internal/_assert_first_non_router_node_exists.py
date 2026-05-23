from __future__ import annotations


def _assert_first_non_router_node_exists(first_node) -> None:
    if first_node is None:
        raise ValueError("Graph has no non-router node — cannot seed task")
