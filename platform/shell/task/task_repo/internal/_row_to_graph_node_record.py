from __future__ import annotations

from shell.task.graph_node_record import GraphNodeRecord


def _row_to_graph_node_record(row: dict) -> GraphNodeRecord:
    return GraphNodeRecord(
        node_id=row["node_id"],
        graph_id=row["graph_id"],
        position=row["position"],
        node_dir=row["node_dir"],
        runner_root_dir=row["runner_root_dir"],
        mode=row["mode"],
        role=row["role"],
        type=row["type"],
        model=row["model"],
        command=row["command"],
        timeout=row["timeout"],
        retries=row["retries"],
        log_level=row["log_level"],
        max_step=row["max_step"],
        no_ask_user=bool(row["no_ask_user"]) if row["no_ask_user"] is not None else None,
        autopilot=bool(row["autopilot"]) if row["autopilot"] is not None else None,
        task_name=row["task_name"],
        source_dir=row["source_dir"],
        work_dir=row["work_dir"],
        status_initial=row["status_initial"],
        extra_json=row["extra_json"],
    )
