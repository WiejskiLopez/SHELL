from __future__ import annotations

from typing import TYPE_CHECKING

from shell.component.prompt_repo.internal._import_prompt_if_changed import _import_prompt_if_changed
from shell.utils.path.path import Path, PathType

if TYPE_CHECKING:
    from shell.component.prompt_repo.prompt_repo import PromptRepo


def _import_task_prompts(
    repo: 'PromptRepo',
    task_id: int,
    task_name: str,
    source_dir: PathType,
) -> int:
    if not Path.is_dir(source_dir):
        return 0
    count = 0
    for path in Path.glob(source_dir, '*.prompt.md'):
        filename = path.name
        kind = _classify_prompt_filename(filename)
        if kind is None:
            continue
        role = _extract_role(filename)
        if role is None and kind != 'skill':
            continue
        body = Path.read_text(path)
        _import_prompt_if_changed(
            repo,
            kind=kind,
            name=filename,
            body=body,
            role=role,
            task_id=task_id,
            source_uri=str(path),
        )
        count += 1
    return count


def _classify_prompt_filename(filename: str) -> str | None:
    if '.system.prompt.md' in filename:
        return 'system'
    if '.skill.prompt.md' in filename:
        return 'skill'
    if '.task.prompt.md' in filename:
        return 'task'
    if '.input.prompt.md' in filename:
        return 'input'
    if filename.endswith('.prompt.md'):
        return 'role'
    return None


def _extract_role(filename: str) -> str | None:
    parts = filename.split('.')
    if not parts:
        return None
    return parts[0] or None
