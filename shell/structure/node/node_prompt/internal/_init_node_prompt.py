from __future__ import annotations

from shell.component.prompt_file.prompt_file import PromptFile


def _init_node_prompt(node_prompt) -> None:
    app = node_prompt._app
    node_prompt._prompt_dir = None
    role = app.app_properties_.role_
    task_name = app.cli_.cli_properties_.task_name_
    if not task_name or role not in ('tasker', 'agent'):
        return
    record = app.task_repo_.get_current_task(task_name)
    if record is None:
        return

    if role == 'tasker':
        entries = app.prompt_repo_.list_prompts_for_task(record.task_id_)
    else:
        role_tag = f'.{role}.'
        entries = []
        for entry in app.prompt_repo_.list_prompts_for_task(record.task_id_):
            if entry.kind_ == 'system':
                if role_tag not in entry.name_:
                    entries.append(entry)
            else:
                if role_tag in entry.name_:
                    entries.append(entry)

    for entry in entries:
        file_prompt = PromptFile()
        file_prompt.init_prompt_file(entry.name_, entry.body_)
        node_prompt.prompt_.file_prompts_.append(file_prompt)
