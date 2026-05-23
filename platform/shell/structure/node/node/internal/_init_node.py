from __future__ import annotations


from shell.structure.node.node.internal._validate_node import _validate_node
from shell.structure.node.node.internal._assert_source_dir_set import _assert_source_dir_set
from shell.utils.path.path import Path, PathType

def _init_node(node, node_dir: str, node_config=None) -> None:
    node._node_dir = node_dir
    node._node_name = Path.new(node_dir).name
    node_dir = node.node_dir_

    node.node_config_.init_node_config()
    node.node_input_.init_node_input()
    node.node_output_.init_node_output()
    node.node_logs_.init_node_logs()
    node.node_archive_.init_node_archive()

    source_dir = node._app.cli_.cli_properties_.source_dir_
    _assert_source_dir_set(source_dir)
    if node._app.cli_.cli_properties_.mode_ == 'agent':
        node.node_prompt_.init_node_prompt()
    if node._app.cli_.cli_properties_.mode_ == 'router':
        node.node_stage_.init_node_stage()
    if node._app.cli_.cli_properties_.mode_ == 'tasker':
        node.node_task_.init_node_task()
    _validate_node(node_dir)
