from __future__ import annotations

from shell.utils.path.path import PathType


from shell.structure.node.node.internal._assert_node_dir_is_dir import _assert_node_dir_is_dir
from shell.structure.node.node.internal._assert_config_yaml_exists import _assert_config_yaml_exists
from shell.constants.constants import DOT_NODE, CONFIG_DIR, CONFIG_YAML


def _validate_node(node_dir: PathType) -> None:
    _assert_node_dir_is_dir(node_dir, '_validate_node')
    _assert_config_yaml_exists(node_dir / DOT_NODE / CONFIG_DIR / CONFIG_YAML)
