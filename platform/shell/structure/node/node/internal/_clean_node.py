from __future__ import annotations


def _clean_node(node) -> None:
    node.node_input_.clean_node_input()
    node.node_output_.clean_node_output()
    node.node_temp_.clean_node_temp()
    node.node_scripts_.clean_node_scripts()
    node.node_logs_.clean_node_logs()
    node.node_stage_.clean_node_stage()
    node.node_archive_.clean_node_archive()
