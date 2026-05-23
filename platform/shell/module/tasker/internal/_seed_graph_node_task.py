from __future__ import annotations

from shell.structure.graph.graph.internal._persist_node_status import _persist_node_status
from shell.status.status import Status
from shell.module.tasker.internal._assert_router_node_exists import _assert_router_node_exists
from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_TASK


def _seed_graph_node_task(tasker) -> None:
    app = tasker._app

    router_node = next(
        (pn for pn in tasker.graph_.sub_nodes_
         if pn.mode_ == 'router'
         and pn.role_ != 'maker'),
        None,
    )
    _assert_router_node_exists(router_node)

    router_node.node_status_.set_status(Status.READY)
    _persist_node_status(router_node, app)
    app.app_trace_.record_info(
        'tasker._seed_graph_node_task',
        f'node {router_node.node_name_} status=READY(8)'
    )

    node_task = app.app_node_.node_.node_task_
    task_name = node_task.task_name_
    task_md_file_body = node_task.task_md_file_body_
    if task_name is None or task_md_file_body is None:
        return

    task_dir = router_node.sub_node_properties_.node_dir_ / DOT_NODE / DIR_TASK
    Path.mkdir(task_dir)
    Path.write_text(task_dir / f'{task_name}.md', task_md_file_body)
    app.app_trace_.record_info(
        'tasker._seed_graph_node_task',
        f'seeded {task_name}.md into {router_node.node_name_} task'
    )
