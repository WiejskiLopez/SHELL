from __future__ import annotations

from shell.component.prompt_file.prompt_file import PromptFile


def _init_prompt_system(prompt_system) -> None:
    app = prompt_system._app
    role = app.app_properties_.role_
    task_name = app.cli_.cli_properties_.task_name_
    prompt_system._file_prompts = []
    record = app.task_repo_.get_current_task(task_name) if task_name else None
    if record is None:
        return
    marker = f'.{role}.{task_name}.'
    for entry in app.prompt_repo_.list_prompts_for_task(record.task_id_, kind='system', role=role):
        if marker not in entry.name_:
            continue
        if not entry.body_:
            continue
        file_prompt = PromptFile()
        file_prompt.init_prompt_file(entry.name_, entry.body_)
        prompt_system._file_prompts.append(file_prompt)
