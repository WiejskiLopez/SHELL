"""_import_task_to_db.py
Resolve <source_dir>/<task_name>.{md,yaml} and import them via TaskRepo.

Returns the (idempotent) TaskRecord. Sets app trace breadcrumbs for the run.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.task.task_record import TaskRecord
from shell.utils.path.path import Path

if TYPE_CHECKING:
    from shell.app.app.app import App


def _import_task_to_db(app: App) -> TaskRecord:
    task_name = app.cli_.cli_properties_.task_name_
    source_dir = Path.new(app.cli_.cli_properties_.source_dir_)
    md_path = source_dir / f"{task_name}.md"
    yaml_path = source_dir / f"{task_name}.yaml"

    record = app.task_repo_.import_task_from_files(
        name=task_name,
        source_md_path=str(md_path),
        source_yaml_path=str(yaml_path),
    )
    prompt_count = app.prompt_repo_.import_task_prompts(
        task_id=record.task_id_,
        task_name=task_name,
        source_dir=source_dir,
    )
    app.app_trace_.record_info(
        'tasker._import_task_to_db',
        f'task_id={record.task_id_} version={record.version_} hash={record.content_hash_[:12]} prompts={prompt_count}',
    )
    return record
