from __future__ import annotations

from typing import TYPE_CHECKING

from shell.task.graph_node_record import GraphNodeRecord
from shell.task.task_repo.internal._row_to_graph_node_record import _row_to_graph_node_record

if TYPE_CHECKING:
    from shell.task.task_repo.task_repo import TaskRepo


def _get_graph_nodes(repo: TaskRepo, task_id: int) -> list[GraphNodeRecord]:
    rows = repo.driver_.query(
        """
        SELECT gn.node_id, gn.graph_id, gn.position, gn.node_dir, gn.runner_root_dir,
               gn.mode, gn.role, gn.type, gn.model, gn.command, gn.timeout, gn.retries,
               gn.log_level, gn.max_step, gn.no_ask_user, gn.autopilot, gn.task_name,
               gn.source_dir, gn.work_dir, gn.status_initial, gn.extra_json
          FROM graph_node gn
          JOIN graph g ON gn.graph_id = g.graph_id
         WHERE g.task_id = ?
         ORDER BY gn.position ASC
        """,
        (task_id,),
    )
    return [_row_to_graph_node_record(r) for r in rows]
