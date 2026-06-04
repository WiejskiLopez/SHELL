"""_load_role_prompt.py
Loads role prompt from DB (PromptRepo). Bootstrap-imports `role_prompts/<role>.md`
package files lazily on first call.
"""


from shell.utils.path.path import Path

_ROLE_PROMPTS_DIR = Path.new(__file__).parent.parent / 'role_prompts'


def _load_role_prompt(prompt) -> None:
    role = prompt._app.app_properties_.role_
    if not role:
        return
    repo = prompt._app.prompt_repo_
    if Path.is_dir(_ROLE_PROMPTS_DIR):
        repo.bootstrap_role_prompts(_ROLE_PROMPTS_DIR)
    record = repo.get_current_prompt(kind='role', name=role, role=role)
    if record is not None:
        prompt._role_prompt = record.body_
