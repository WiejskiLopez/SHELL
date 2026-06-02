from __future__ import annotations

from typing import TYPE_CHECKING

from shell.component.prompt_repo.internal._row_to_prompt_record import _row_to_prompt_record
from shell.component.prompt_repo.prompt_record import PromptRecord

if TYPE_CHECKING:
    from shell.component.prompt_repo.prompt_repo import PromptRepo


def _get_prompt_by_id(repo: 'PromptRepo', prompt_id: int) -> PromptRecord | None:
    rows = repo.driver_.query(
        'SELECT prompt_id, kind, task_id, role, name, body, content_hash, '
        'source_uri, version, is_current, created_at FROM prompt WHERE prompt_id = ?',
        (prompt_id,),
    )
    return _row_to_prompt_record(rows[0]) if rows else None
