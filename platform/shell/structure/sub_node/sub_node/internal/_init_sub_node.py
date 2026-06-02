from __future__ import annotations

from shell.component.config.config.config import Config
from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_TASK
from shell.status.status import Status


def _init_sub_node(sub_node, sub_node_config_dict, writer, reader) -> None:
    config = Config(sub_node._app)
    config.append_config_dict(sub_node_config_dict, 'sub_node')
    sub_node._sub_node_config = config
    sub_node.sub_node_properties_.init_sub_node_properties(
        sub_node_config_dict,
        writer=writer,
    )
    task_dir = Path.resolve(sub_node._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TASK)
    sub_node.init_sub_node_command(task_dir)
    sub_node.node_status_.init_status(sub_node_config_dict.get('status'))
    if sub_node.status_ == Status.NULL:
        sub_node.node_status_.set_status(Status.INITIALIZED)
        sub_node_config_dict['status'] = Status.INITIALIZED.name
        config.append_config_value('status', Status.INITIALIZED.name, 'sub_node')