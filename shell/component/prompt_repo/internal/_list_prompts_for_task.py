from __future__ import annotations

from typing import TYPE_CHECKING

from shell.component.prompt_repo.internal._row_to_prompt_record import _row_to_prompt_record
from shell.component.prompt_repo.prompt_record import PromptRecord

if TYPE_CHECKING:
    from shell.component.prompt_repo.prompt_repo import PromptRepo


def _list_prompts_for_task(
    repo: 'PromptRepo',
    task_id: int,
    kind: str | None = None,
    role: str | None = None,
) -> list[PromptRecord]:
    where = ['task_id = ?', 'is_current = 1']
    params: list = [task_id]
    if kind is not None:
        where.append('kind = ?')
        params.append(kind)
    if role is not None:
        where.append('role = ?')
        params.append(role)
    sql = (
        'SELECT prompt_id, kind, task_id, role, name, body, content_hash, '
        'source_uri, version, is_current, created_at FROM prompt WHERE '
        + ' AND '.join(where)
        + ' ORDER BY name'
    )
    rows = repo.driver_.query(sql, tuple(params))
    return [_row_to_prompt_record(r) for r in rows]
