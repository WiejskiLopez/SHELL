"""init_system_prompt.py  (prompt)
Responsible for one thing: ensuring the agent's input/ contains a system
prompt file matching its role.

Called during init phase (agent mode), after handle_config and before
build_prompt.  If the agent already has a system prompt in input/, does
nothing.  If a matching template exists in system_prompts/, writes it as
0000_system_<role>.md into input/.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from shell.utils.io.io import default_read_utf8, default_write_utf8
from shell.module.agent.agent_prompt.internal._assert_role_set import _assert_role_set
from shell.module.agent.agent_prompt.internal._has_system_prompt import _has_system_prompt
from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE, DIR_INPUT

_SYSTEM_PROMPTS_DIR = Path.new(__file__).parent / 'role_prompts'
_SYSTEM_PROMPT_PATTERN = re.compile(r'^\d{4}_system_(?P<role>[^.]+)\.md$')


def init_system_prompt(app: dict, reader: Callable[[PathType], str] | None = None, writer: Callable[[PathType, str], None] | None = None) -> None:
    """Write 0000_system_<role>.md to agent input/ if not already present.

    Silently skips when:
    - no template exists for the given role
    - a system prompt for this role already exists in input/

    reader: optional callable (path: PathType) -> str for testability.
    writer: optional callable (path: PathType, content: str) -> None for testability.
    """
    if reader is None:
        reader = default_read_utf8
    if writer is None:
        writer = default_write_utf8

    try:
        role = app.app_node_.node_.role
        _assert_role_set(role)

        node_dir = app.app_node_.node_.node_dir_
        input_dir = node_dir / DOT_NODE / DIR_INPUT

        if _has_system_prompt(input_dir, role):
            return

        template_path = _SYSTEM_PROMPTS_DIR / f'{role}.md'
        if not Path.is_file(template_path):
            raise FileNotFoundError(f"[init_system_prompt] No system prompt template for role '{role}': {template_path}")

        content = reader(template_path)
        app.app_trace_.record_info('agent_prompt.load_system_prompt.load_system_prompt', f'read {template_path}')
        Path.mkdir(input_dir)
        target = input_dir / f'0000_system_{role}.md'
        writer(target, content)
        app.app_trace_.record_info('agent_prompt.load_system_prompt.load_system_prompt', f'write {target}')
    except Exception as exc:
        app.app_trace_.record_error_and_raise('agent_prompt.load_system_prompt.load_system_prompt', exc)
