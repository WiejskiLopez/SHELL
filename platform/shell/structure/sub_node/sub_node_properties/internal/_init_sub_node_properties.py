from __future__ import annotations

from shell.structure.node.node.internal._validate_node import _validate_node


def _init_sub_node_properties(sub_node_properties, sub_node_config_dict: dict, writer=None) -> None:
    sub_node_properties.sub_node_dir_ = sub_node_config_dict['sub_node_dir']
    sub_node_properties.sub_node_runner_root_dir_ = sub_node_config_dict.get('runner_root_dir')
    node_dir = sub_node_properties.node_dir_
    runner_root_dir = sub_node_config_dict['runner_root_dir']
    sub_node_properties.sub_node_node_config_.append_node_config(node_dir, sub_node_config_dict, runner_root_dir, overwrite=True, writer=writer)
    _validate_node(node_dir)
    config_dict = sub_node_properties.sub_node_node_config_.config_.config_dict_
    sub_node_properties._name = config_dict.get('name')
    sub_node_properties._mode = config_dict.get('mode')
    sub_node_properties._role = config_dict.get('role')
    sub_node_properties._type = config_dict.get('type')
    sub_node_properties._model = config_dict.get('model')
    sub_node_properties._command = config_dict.get('command')
    sub_node_properties._timeout = config_dict.get('timeout')
    sub_node_properties._retries = config_dict.get('retries')
    sub_node_properties._log_level = config_dict.get('log_level')
    sub_node_properties._max_step = config_dict.get('max_step')
    sub_node_properties._no_ask_user = config_dict.get('no_ask_user')
    sub_node_properties._autopilot = config_dict.get('autopilot')
    sub_node_properties._task_name = config_dict.get('task_name')
    sub_node_properties._source_dir = config_dict.get('source_dir')
    sub_node_properties._work_dir = config_dict.get('work_dir')
