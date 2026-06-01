from __future__ import annotations


from shell.component.prompt_file.prompt_file import PromptFile
from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE, DIR_PROMPT


def _init_prompt_role(prompt_role) -> None:
    app = prompt_role._app
    task_dir = Path.new(app.cli_.cli_properties_.source_dir_ or app.cli_.cli_properties_.task_dir_)
    role = app.app_properties_.role_
    task_name = app.cli_.cli_properties_.task_name_
    prompt_dir = app.app_node_.node_.node_dir_ / DOT_NODE / DIR_PROMPT
    prompt_role._file_prompts = []
    marker = f'.{role}.{task_name}.'
    for path in Path.glob(task_dir, '*.prompt.md'):
        if '.system.' in path.name:
            continue
        if marker not in path.name:
            continue
        body = Path.read_text(path)
        if body:
            file_prompt = PromptFile()
            file_prompt.init_prompt_file(path.name, body, prompt_dir)
            prompt_role._file_prompts.append(file_prompt)
