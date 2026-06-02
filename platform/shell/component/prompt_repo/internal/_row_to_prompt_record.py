from __future__ import annotations

from shell.component.prompt_repo.prompt_record import PromptRecord


def _row_to_prompt_record(row: dict) -> PromptRecord:
    return PromptRecord(
        prompt_id=row['prompt_id'],
        kind=row['kind'],
        task_id=row['task_id'],
        role=row['role'],
        name=row['name'],
        body=row['body'],
        content_hash=row['content_hash'],
        source_uri=row['source_uri'],
        version=row['version'],
        is_current=row['is_current'],
        created_at=row['created_at'],
    )
