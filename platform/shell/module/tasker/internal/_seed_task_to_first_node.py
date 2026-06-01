from __future__ import annotations

from shell.module.tasker.internal._assert_first_non_router_node_exists import _assert_first_non_router_node_exists
from shell.module.tasker.internal._assert_task_files_exist import _assert_task_files_exist
from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_INPUT


def _seed_task_to_first_node(tasker, task_dir) -> None:
    sub_nodes = tasker.graph_.sub_nodes_
    first_node = next((pn for pn in sub_nodes if pn.mode_ != 'router'), None)
    _assert_first_non_router_node_exists(first_node)
    task_files = Path.glob(task_dir, '*.md') if Path.exists(task_dir) else []
    _assert_task_files_exist(task_dir, task_files)
    input_dir = first_node.sub_node_properties_.node_dir_ / DOT_NODE / DIR_INPUT
    Path.mkdir(input_dir)
    for task_file in task_files:
        Path.copy_to(task_file, input_dir / task_file.name)
    tasker._app.app_trace_.record_info(
        'tasker._run_iterative_tasker._seed_task_to_first_node',
        f'seeded {len(task_files)} file(s) from task_dir to {first_node.node_name_} input'
    )
