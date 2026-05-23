from __future__ import annotations

import yaml

from shell.status.status import Status
from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_TASK


def _init_new_node_statuses(tasker) -> None:
    app = tasker._app
    task_dir = (app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TASK).resolve()
    yaml_files = Path.glob(task_dir, '*.yaml')
    if not yaml_files:
        return
    yaml_path = yaml_files[0]

    initialized_nodes = [pn for pn in tasker.graph_.sub_nodes_ if pn.status_ == Status.INITIALIZED]
    if not initialized_nodes:
        return

    data = yaml.safe_load(Path.read_text(yaml_path)) or {}
    for graph_node in initialized_nodes:
        for node_dict in data.get('graph', []):
            if node_dict.get('node_name') == graph_node.node_name_:
                node_dict['status'] = Status.INITIALIZED.name
                break

    Path.write_text(yaml_path, yaml.dump(data, default_flow_style=False, allow_unicode=True))
    app.app_trace_.record_info(
        'tasker._init_new_node_statuses._init_new_node_statuses',
        f'persisted INITIALIZED for {len(initialized_nodes)} new node(s) to {yaml_path.name}'
    )
