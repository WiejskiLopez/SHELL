from __future__ import annotations
from shell.constants.constants import DOT_NODE, DIR_PROMPT


def _init_prompt(prompt) -> None:
    app = prompt._app
    prompt._prompt_dir = app.app_node_.node_.node_dir_ / DOT_NODE / DIR_PROMPT

    cli_prompt = app.cli_.cli_properties_.prompt_
    if cli_prompt is not None:
        prompt.prompt_cli_.init_prompt_cli()

    prompt.prompt_role_.init_prompt_role()
    prompt.prompt_skill_.init_prompt_skill()
    prompt.prompt_system_.init_prompt_system()
    prompt.prompt_task_.init_prompt_task()
    prompt.prompt_input_.init_prompt_input()
