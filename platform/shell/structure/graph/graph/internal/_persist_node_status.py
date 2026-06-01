from __future__ import annotations

import yaml

from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE, DIR_TASK


def _persist_node_status(sub_node, app) -> None:
    task_dir = (app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TASK).resolve()
    yaml_files = Path.glob(task_dir, '*.yaml')
    if not yaml_files:
        return
    yaml_path = yaml_files[0]
    data = yaml.safe_load(Path.read_text(yaml_path)) or {}
    for node_dict in data.get('graph', []):
        if node_dict.get('node_name') == sub_node.node_name_:
            node_dict['status'] = sub_node.status_.name
            break
    Path.write_text(yaml_path, yaml.dump(data, default_flow_style=False, allow_unicode=True))
    app.app_trace_.record_info(
        'graph._persist_node_status._persist_node_status',
        f'persisted status={sub_node.status_.name} for node {sub_node.node_name_} to {yaml_path.name}'
    )
