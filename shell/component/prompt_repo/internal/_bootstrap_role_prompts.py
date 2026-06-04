from __future__ import annotations

from typing import TYPE_CHECKING

from shell.component.prompt_repo.internal._import_prompt_if_changed import _import_prompt_if_changed
from shell.utils.path.path import Path, PathType

if TYPE_CHECKING:
    from shell.component.prompt_repo.prompt_repo import PromptRepo


def _bootstrap_role_prompts(repo: 'PromptRepo', role_prompts_dir: PathType) -> int:
    if not Path.is_dir(role_prompts_dir):
        return 0
    count = 0
    for path in Path.glob(role_prompts_dir, '*.md'):
        role_name = path.stem
        body = Path.read_text(path)
        _import_prompt_if_changed(
            repo,
            kind='role',
            name=role_name,
            body=body,
            role=role_name,
            task_id=None,
            source_uri=str(path),
        )
        count += 1
    return count
