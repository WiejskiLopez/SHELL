from __future__ import annotations

from typing import TYPE_CHECKING

from shell.task.task_record import TaskRecord
from shell.task.task_repo.internal._row_to_task_record import _row_to_task_record

if TYPE_CHECKING:
    from shell.task.task_repo.task_repo import TaskRepo


def _get_current_task(repo: TaskRepo, name: str) -> TaskRecord | None:
    rows = repo.driver_.query(
        """
        SELECT task_id, name, version, content_hash, body_md, body_yaml_raw,
               source_md_uri, source_yaml_uri, is_current, created_at
          FROM task
         WHERE name = ? AND is_current = 1
         LIMIT 1
        """,
        (name,),
    )
    if not rows:
        return None
    return _row_to_task_record(rows[0])
