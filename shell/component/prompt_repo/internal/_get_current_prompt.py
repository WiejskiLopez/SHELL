from __future__ import annotations

from typing import TYPE_CHECKING

from shell.component.prompt_repo.internal._row_to_prompt_record import _row_to_prompt_record
from shell.component.prompt_repo.prompt_record import PromptRecord

if TYPE_CHECKING:
    from shell.component.prompt_repo.prompt_repo import PromptRepo


def _get_current_prompt(
    repo: 'PromptRepo',
    kind: str,
    name: str,
    role: str | None = None,
    task_id: int | None = None,
) -> PromptRecord | None:
    where = ['kind = ?', 'name = ?', 'is_current = 1']
    params: list = [kind, name]
    if role is None:
        where.append('role IS NULL')
    else:
        where.append('role = ?')
        params.append(role)
    if task_id is None:
        where.append('task_id IS NULL')
    else:
        where.append('task_id = ?')
        params.append(task_id)
    sql = (
        'SELECT prompt_id, kind, task_id, role, name, body, content_hash, '
        'source_uri, version, is_current, created_at FROM prompt WHERE '
        + ' AND '.join(where)
        + ' LIMIT 1'
    )
    rows = repo.driver_.query(sql, tuple(params))
    return _row_to_prompt_record(rows[0]) if rows else None
