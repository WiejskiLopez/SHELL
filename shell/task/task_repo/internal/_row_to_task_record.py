from __future__ import annotations

from shell.task.task_record import TaskRecord


def _row_to_task_record(row: dict) -> TaskRecord:
    return TaskRecord(
        task_id=row["task_id"],
        name=row["name"],
        version=row["version"],
        content_hash=row["content_hash"],
        body_md=row["body_md"],
        body_yaml_raw=row["body_yaml_raw"],
        source_md_uri=row["source_md_uri"],
        source_yaml_uri=row["source_yaml_uri"],
        is_current=bool(row["is_current"]),
        created_at=row["created_at"],
    )
