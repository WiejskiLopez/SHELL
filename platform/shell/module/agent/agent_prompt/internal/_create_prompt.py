from shell.module.agent.agent_prompt.internal._build_prompt_from_input import _build_prompt_from_input
from shell.module.agent.agent_prompt.internal._resolve_prompt import _resolve_prompt


def _create_prompt(app, reader=None) -> str:
    """Build and return the prompt string.

    If --prompt is set, delegates to _resolve_prompt (text / file / directory).
    Otherwise builds from node's input/ directory.
    reader: optional callable (path: Path) -> str for testability.
    """
    cli_prompt = app.cli_.cli_properties_.prompt_
    if cli_prompt is not None:
        return _resolve_prompt(cli_prompt, app.app_node_.node_.node_dir_, reader=reader)
    return _build_prompt_from_input(app)
