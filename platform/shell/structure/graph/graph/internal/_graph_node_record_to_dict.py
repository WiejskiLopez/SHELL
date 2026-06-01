"""_graph_node_record_to_dict.py
Convert a GraphNodeRecord (DB DTO) into the dict shape historically produced by
parsing task.yaml's `graph:` entries. Keeps SubNodeProperties pipeline unchanged.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.task.graph_node_record import GraphNodeRecord


def _graph_node_record_to_dict(record: GraphNodeRecord) -> dict:
    out: dict = {
        'sub_node_dir': record.node_dir_,
        'node_dir': record.node_dir_,
        'runner_root_dir': record.runner_root_dir_,
        'mode': record.mode_,
        'role': record.role_,
        'type': record.type_,
        'model': record.model_,
        'command': record.command_,
        'timeout': record.timeout_,
        'retries': record.retries_,
        'log_level': record.log_level_,
        'max_step': record.max_step_,
        'no_ask_user': record.no_ask_user_,
        'autopilot': record.autopilot_,
        'task_name': record.task_name_,
        'source_dir': record.source_dir_,
        'work_dir': record.work_dir_,
        'status': record.status_initial_,
    }
    if record.extra_json_:
        try:
            extra = json.loads(record.extra_json_)
            if isinstance(extra, dict):
                for key, value in extra.items():
                    if key not in out or out[key] is None:
                        out[key] = value
        except (ValueError, TypeError):
            pass
    return out
