"""_init_role_prompt.py
Private. Responsible for one thing: loading a role prompt file from
role_prompts/<role>.md into the Prompt instance.
"""


from shell.utils.path.path import Path, PathType

_ROLE_PROMPTS_DIR = Path.new(__file__).parent.parent / 'role_prompts'


def _init_role_prompt(prompt) -> None:
    role = prompt._app.app_properties_.role_
    if role:
        template = _ROLE_PROMPTS_DIR / f'{role}.md'
        if Path.is_file(template):
            prompt._role_prompt = Path.read_text(template)
