from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from shell.component.prompt_repo.internal._compute_prompt_hash import _compute_prompt_hash
from shell.component.prompt_repo.internal._get_current_prompt import _get_current_prompt
from shell.component.prompt_repo.internal._get_prompt_by_id import _get_prompt_by_id
from shell.component.prompt_repo.prompt_record import PromptRecord

if TYPE_CHECKING:
    from shell.component.prompt_repo.prompt_repo import PromptRepo


def _import_prompt_if_changed(
    repo: 'PromptRepo',
    kind: str,
    name: str,
    body: str,
    role: str | None = None,
    task_id: int | None = None,
    source_uri: str | None = None,
) -> PromptRecord:
    content_hash = _compute_prompt_hash(kind, role, name, body)
    current = _get_current_prompt(repo, kind=kind, name=name, role=role, task_id=task_id)
    if current is not None and current.content_hash_ == content_hash:
        return current

    next_version = 1 if current is None else _max_version(repo, kind, name, role, task_id) + 1
    now = datetime.now(timezone.utc).isoformat()

    driver = repo.driver_
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
    driver.execute(
        'UPDATE prompt SET is_current = 0 WHERE ' + ' AND '.join(where),
        tuple(params),
    )
    driver.execute(
        'INSERT INTO prompt (kind, task_id, role, name, body, content_hash, '
        'source_uri, version, is_current, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)',
        (kind, task_id, role, name, body, content_hash, source_uri, next_version, now),
    )
    new_id = driver.last_insert_id()
    driver.commit()
    return _get_prompt_by_id(repo, new_id)


def _max_version(
    repo: 'PromptRepo',
    kind: str,
    name: str,
    role: str | None,
    task_id: int | None,
) -> int:
    where = ['kind = ?', 'name = ?']
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
    sql = 'SELECT COALESCE(MAX(version), 0) AS v FROM prompt WHERE ' + ' AND '.join(where)
    rows = repo.driver_.query(sql, tuple(params))
    return rows[0]['v'] if rows else 0
