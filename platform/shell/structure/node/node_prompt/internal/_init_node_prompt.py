from __future__ import annotations


from shell.utils.path.path import Path, PathType
from shell.component.prompt_file.prompt_file import PromptFile
from shell.constants.constants import DOT_NODE, DIR_PROMPT


def _init_node_prompt(node_prompt) -> None:
    app = node_prompt._app
    node_prompt._prompt_dir = (app.app_node_.node_.node_dir_ / DOT_NODE / DIR_PROMPT).resolve()
    task_dir = Path.new(app.cli_.cli_properties_.task_dir_)
    role = app.app_properties_.role_
    if role == 'tasker':
        paths = Path.glob(task_dir, '*.prompt.md')
    elif role == 'agent':
        paths = []
        role_tag = f'.{role}.'
        for path in Path.glob(task_dir, '*.prompt.md'):
            name = path.name
            if '.system.' in name:
                if role_tag not in name:
                    paths.append(path)
            else:
                if role_tag in name:
                    paths.append(path)
    else:
        return
    for path in paths:
        file_prompt = PromptFile()
        file_prompt.init_prompt_file(path.name, Path.read_text(path), node_prompt._prompt_dir)
        node_prompt.prompt_.file_prompts_.append(file_prompt)
