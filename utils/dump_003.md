### platform/shell/module/agent/agent_prompt/internal/_init_agent_prompt.py
```
from __future__ import annotations


from shell.module.agent.agent_prompt.internal._assert_task_dir_resolved import _assert_task_dir_resolved
from shell.module.agent.agent_prompt.internal._assert_role_resolved import _assert_role_resolved
from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE, DIR_PROMPT


def _init_agent_prompt(agent_prompt) -> None:
    app = agent_prompt._app
    task_dir = app.cli_.cli_properties_.task_dir_
    source_dir = app.cli_.cli_properties_.source_dir_
    app.app_trace_.record_info('agent_prompt._init_agent_prompt._init_agent_prompt', f'task_dir={task_dir}, source_dir={source_dir}')
    role = app.app_properties_.role_
    _assert_task_dir_resolved(task_dir)
    _assert_role_resolved(role)
    prompt_dir = app.app_node_.node_.node_dir_ / DOT_NODE / DIR_PROMPT

    cli_prompt = app.cli_.cli_properties_.prompt_
    app.app_trace_.record_info('agent_prompt._init_agent_prompt._init_agent_prompt', f'cli_prompt set={cli_prompt is not None}')
    if cli_prompt is not None:
        agent_prompt.prompt_cli_.init_prompt_cli(app)
        app.app_trace_.record_info('agent_prompt._init_agent_prompt._init_agent_prompt', 'using cli prompt — skipping role/system prompt loading')
        return

    prompt_source = source_dir if source_dir is not None else task_dir
    prompt_source_files = [p.name for p in Path.iterdir(Path.new(prompt_source)) if Path.is_file(p)]
    app.app_trace_.record_info(
        'agent_prompt._init_agent_prompt._init_agent_prompt',
        f'prompt_source files: {prompt_source_files}'
    )

    app.app_trace_.record_info(
        'agent_prompt._init_agent_prompt._init_agent_prompt',
        f'loading role prompts from {prompt_source} pattern *.prompt.md (excluding *.system.*)'
    )
    task_name = app.cli_.cli_properties_.task_name_
    agent_prompt.prompt_role_.init_prompt_role(prompt_source, role, task_name, prompt_dir)
    app.app_trace_.record_info(
        'agent_prompt._init_agent_prompt._init_agent_prompt',
        f'role prompts loaded: {[p.file_name_ for p in agent_prompt.prompt_role_.file_prompts_]}'
    )

    app.app_trace_.record_info(
        'agent_prompt._init_agent_prompt._init_agent_prompt',
        f'loading system prompts from {prompt_source} pattern *.system.prompt.md (role={role}, task_name={task_name})'
    )
    agent_prompt.prompt_skill_.init_prompt_skill(prompt_source, task_name, prompt_dir)
    app.app_trace_.record_info(
        'agent_prompt._init_agent_prompt._init_agent_prompt',
        f'skill prompts loaded: {[p.file_name_ for p in agent_prompt.prompt_skill_.file_prompts_]}'
    )

    agent_prompt.prompt_system_.init_prompt_system(prompt_source, role, task_name, prompt_dir)
    app.app_trace_.record_info(
        'agent_prompt._init_agent_prompt._init_agent_prompt',
        f'system prompts loaded: {[p.file_name_ for p in agent_prompt.prompt_system_.file_prompts_]}'
    )
```

### platform/shell/module/agent/agent_prompt/internal/_load_role_prompt.py
```
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
```

### platform/shell/module/agent/agent_prompt/internal/_resolve_prompt.py
```
from __future__ import annotations


from shell.utils.io.io import default_read_utf8_safe
from shell.module.agent.agent_prompt.internal._build_from_dir import _build_from_dir
from shell.module.agent.agent_prompt.internal._find_file import _find_file
from shell.utils.path.path import Path, PathType


def _resolve_prompt(value: str, node: PathType, reader=None) -> str:
    if reader is None:
        reader = default_read_utf8_safe
    path = Path.new(value)

    if Path.is_file(path):
        return reader(path)

    if Path.is_dir(path):
        return _build_from_dir(path, reader=reader)

    if len(path.parts) == 1:
        found_file = _find_file(value, node)
        if found_file:
            return reader(found_file)

    return value
```

### platform/shell/module/agent/agent_prompt/load_system_prompt.py
```
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
```

### platform/shell/module/agent/agent_prompt/role_prompts/analyzer.md
```
You are an **analyzer** agent.
Your role is to analyze the provided input and produce a structured report.
- Identify patterns, problems, and opportunities
- Summarize findings clearly with supporting evidence
- Output a structured markdown report
```

### platform/shell/module/agent/agent_prompt/role_prompts/architect.md
```
You are an **architect** agent.
Your role is to design the solution architecture based on the task description.
- Produce a clear architectural blueprint with component diagram (text or ASCII)
- Define interfaces, data flows, and responsibilities of each component
- Output a single markdown architecture document
```

### platform/shell/module/agent/agent_prompt/role_prompts/developer.md
```
You are a **developer** agent.
Your role is to implement the solution based on the provided draft or task description.
- Implement all TODOs and stubs left by previous agents
- Write clean, idiomatic, production-quality code
- Add unit tests covering happy path and edge cases
- Output one file per deliverable
```

### platform/shell/module/agent/agent_prompt/role_prompts/maker.md
```
You are a **maker** agent.
Your role is to prepare a clear, well-structured draft or scaffold based on the task description.
- Produce a skeleton with correct structure, signatures, and docstrings
- Do not implement the full logic — leave TODOs where implementation is needed
- Output one file per deliverable
- Be concise and precise
```

### platform/shell/module/agent/agent_prompt/role_prompts/reviewer.md
```
You are a **reviewer** agent.
Your role is to review the provided code or document for quality, correctness, and completeness.
- Check for bugs, edge cases, and missing error handling
- Verify tests are present and meaningful
- Suggest concrete improvements with code examples
- Output a review report as a single markdown file
```

### platform/shell/module/agent/agent_prompt/role_prompts/tester.md
```
You are a **tester** agent.
Your role is to write and execute tests for the provided implementation.
- Write unit tests, integration tests, and edge case tests
- Ensure all tests pass before outputting
- Output test files and a short test report
```

### platform/shell/module/agent/agent_properties/__init__.py
```
```

### platform/shell/module/agent/agent_properties/agent_properties.py
```
"""Agent execution parameters: model, timeout, retries, retry_delay."""

from __future__ import annotations


class AgentProperties:
    """Holds Agent runtime parameters extracted from YAML config."""

    __slots__ = ("_app", "_model", "_timeout", "_retries", "_retry_delay")

    def __init__(self, app) -> None:
        self._app = app
        self._model: str | None = None
        self._timeout: int | None = None
        self._retries: int | None = None
        self._retry_delay: float | None = None

    @property
    def model_(self) -> str | None:
        """Return the Agent model name."""
        return self._model

    @property
    def timeout_(self) -> int:
        """Return the Agent timeout in seconds (default 300)."""
        return self._timeout if self._timeout is not None else 300

    @property
    def retries_(self) -> int:
        """Return the number of retries (default 0)."""
        return self._retries if self._retries is not None else 0

    @property
    def retry_delay_(self) -> float:
        """Return the delay between retries in seconds (default 2.0)."""
        return float(self._retry_delay) if self._retry_delay is not None else 2.0

    def init_agent_properties(self) -> None:
        app_properties = self._app.app_properties_
        self._model = app_properties.model_
        self._timeout = app_properties.timeout_
        self._retries = app_properties.retries_
```

### platform/shell/module/router/__init__.py
```
from shell.module.router.router.router import Router
```

### platform/shell/module/router/router/__init__.py
```
from shell.module.router.router.router import Router
```

### platform/shell/module/router/router/build_frontmatter.py
```
def build_frontmatter(content: str, source: str, target: str, timestamp: str, task_id: str) -> str:
    """Prepend YAML frontmatter block to content."""
    frontmatter = (
        f"---\n"
        f"source: {source}\n"
        f"target: {target}\n"
        f"timestamp: {timestamp}\n"
        f"task_id: {task_id}\n"
        f"---\n\n"
    )
    return frontmatter + content
```

### platform/shell/module/router/router/collect_source_files.py
```

from shell.utils.path.path import Path, PathType


def collect_source_files(prev_output_dir: PathType) -> list[PathType]:
    if not Path.is_dir(prev_output_dir):
        return []
    return [f for f in Path.iterdir(prev_output_dir) if Path.is_file(f)]
```

### platform/shell/module/router/router/frontmatter.py
```
"""frontmatter.py
Responsible for one thing: parsing YAML front-matter from text.
"""

from __future__ import annotations

import re
from typing import Dict, Optional, Tuple

import yaml


def parse_frontmatter(text: str) -> Tuple[Optional[Dict], str]:
    """Parse YAML front-matter. Returns (data, body) or (None, text) on parse failure."""
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end == -1:
        return None, text
    fm_text = text[3:end].strip()
    body = text[end + 4:]
    try:
        data = yaml.safe_load(fm_text)
        return data, body
    except yaml.YAMLError:
        return None, text
```

### platform/shell/module/router/router/get_role_to_node_map.py
```
def get_role_to_node_map(graph: list) -> dict[str, dict]:
    """Return mapping of role -> node for all nodes that have a role defined."""
    return {n['role']: n for n in graph if n.get('role')}
```

### platform/shell/module/router/router/get_target_role_from_filename.py
```
from shell.utils.path.path import Path, PathType


def get_target_role_from_filename(filename: str, roles: set) -> str | None:
    """Return role if the stem ends with _<role>, else None."""
    stem = Path.new(filename).stem
    parts = stem.rsplit('_', 1)
    if len(parts) == 2 and parts[-1] in roles:
        return parts[-1]
    return None
```

### platform/shell/module/router/router/internal/__init__.py
```
```

### platform/shell/module/router/router/internal/_assert_active_file_parsed.py
```
from shell.utils.path.path import PathType

from shell.module.router.router.parse_message_filename import MessageFilename


def _assert_active_file_parsed(parsed: MessageFilename | None, active_file: PathType) -> None:
    if parsed is None:
        raise ValueError(f"[Router] active file has unparseable filename: '{active_file.name}'")
    if not parsed.from_role:
        raise ValueError(f"[Router] active file has no from_role in filename: '{active_file.name}'")
```

### platform/shell/module/router/router/internal/_assert_graph_node_role_set.py
```
def _assert_graph_node_role_set(role: str | None, node_name: str) -> None:
    if not role:
        raise ValueError(f"[Router] graph node '{node_name}' has no role defined")
```

### platform/shell/module/router/router/internal/_assert_node_in_graph.py
```
"""_assert_node_in_graph.py
Responsible for one thing: raising ValueError when a node id is not found in the graph.
"""


def _assert_node_in_graph(index, node_id: str) -> None:
    """Raise ValueError if index is None (node not found in graph)."""
    if index is None:
        raise ValueError(f"node '{node_id}' not found in graph")
```

### platform/shell/module/router/router/internal/_assert_role_set.py
```
"""_assert_role_set.py
Responsible for one thing: raising ValueError when a graph node has no role defined.
"""


def _assert_role_set(role: str | None, node: dict) -> None:
    """Raise ValueError if role is falsy."""
    if not role:
        raise ValueError(f"[Router] node '{node.get('id', '?')}' has no role defined")
```

### platform/shell/module/router/router/internal/_assert_router_base_set.py
```
def _assert_router_base_set(value) -> None:
    if value is None:
        raise ValueError("router_base not initialized — call init_router() first")
```

### platform/shell/module/router/router/internal/_assert_step_within_ttl.py
```
from shell.module.router.router.parse_message_filename import MessageFilename


def _assert_step_within_ttl(parsed: MessageFilename, max_step: int) -> None:
    try:
        step = int(parsed.step)
    except (ValueError, TypeError):
        return
    if step >= max_step:
        raise RuntimeError(
            f"TTL exceeded: message '{parsed.sequence_id}__{parsed.from_role}__{parsed.to_role}' "
            f"has step={step} >= max_step={max_step}"
        )
```

### platform/shell/module/router/router/internal/_distribute_active.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

from shell.structure.graph.graph.internal._persist_node_status import _persist_node_status
from shell.module.router.router.parse_message_filename import increment_step
from shell.module.router.router.parse_message_filename import parse_message_filename
from shell.status.status import Status
from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_INPUT

if TYPE_CHECKING:
    from shell.module.router.router.router import Router


def _distribute_active(router: 'Router', node_stage, graph_nodes, app) -> None:
    active_files = node_stage.get_active_files()
    app.app_trace_.record_info('router._distribute_active', f'distributing {len(active_files)} active file(s)')
    for active_file in active_files:
        active_parsed = parse_message_filename(active_file.name)
        target_role = active_parsed.to_role if active_parsed is not None else None
        target_node = (
            router.router_base_.role_to_node_map_.get(target_role) if target_role
            else router.get_next_graph_node()
        )
        if target_node is None:
            continue
        distributed_name = increment_step(active_parsed) if active_parsed is not None else active_file.name
        dest_dir = app.app_node_.node_.node_dir_.parent / target_node.node_name_ / DOT_NODE / DIR_INPUT
        Path.mkdir(dest_dir)
        Path.copy_to(active_file, dest_dir / distributed_name)
        app.app_trace_.record_info(
            'router._distribute_active',
            f'copied {active_file.name} -> node={target_node.node_name_} dir={dest_dir}'
        )
        target_graph_node = next(
            (pn for pn in graph_nodes if pn.role_ == target_role),
            None,
        ) if target_role else next(
            (pn for pn in graph_nodes if pn.mode_ == 'agent'),
            None,
        )
        if target_graph_node is not None:
            target_graph_node.node_status_.set_status(Status.READY)
            _persist_node_status(target_graph_node, app)
            app.app_trace_.record_info(
                'router._run_router._run_router',
                f'node {target_graph_node.node_name_} status=READY'
            )
        if active_parsed is not None and active_parsed.msg_type == 'QUESTION':
            node_stage.move_to_pending(active_file.name)
        else:
            node_stage.move_to_history(active_file.name)
```

### platform/shell/module/router/router/internal/_expire_pending_ttl.py
```
from __future__ import annotations

from shell.module.router.router.parse_message_filename import parse_message_filename


def _expire_pending_ttl(app, node_stage, max_step: int) -> None:
    for pending_file in node_stage.get_pending_files():
        pending_parsed = parse_message_filename(pending_file.name)
        if pending_parsed is not None:
            try:
                if int(pending_parsed.step) > max_step:
                    app.app_trace_.record_info(
                        'router._expire_pending_ttl',
                        f'pending expired ttl: {pending_file.name}'
                    )
                    node_stage.move_to_ignored(pending_file.name)
            except ValueError:
                pass
```

### platform/shell/module/router/router/internal/_flush_done.py
```
from __future__ import annotations

from shell.module.router.router.parse_message_filename import SEPARATOR
from shell.module.router.router.parse_message_filename import parse_message_filename
from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_OUTPUT


def _flush_done(app, node_stage) -> None:
    app.app_trace_.record_info('router._flush_done', 'no agent output and active/ empty — flushing')
    last_message = node_stage.get_last_message()
    if last_message is not None:
        node_dir = app.app_node_.node_.node_dir_
        own_output_dir = node_dir / DOT_NODE / DIR_OUTPUT
        Path.mkdir(own_output_dir)
        parsed = parse_message_filename(last_message.name)
        if parsed is not None and parsed.msg_type == 'DONE':
            output_name = SEPARATOR.join([
                parsed.sequence_id,
                parsed.from_role,
                'analizer',
                'TASK',
                parsed.intent,
                parsed.thread_id,
                app.cli_.cli_properties_.message_id_,
                parsed.step,
            ]) + parsed.suffix
        else:
            output_name = last_message.name
        destination = own_output_dir / output_name
        Path.copy_to(last_message, destination)
        app.app_trace_.record_info('router._flush_done', f'copied {last_message.name} to {destination}')
    else:
        app.app_trace_.record_info('router._flush_done', 'no last message in history')
    app.app_trace_.record_info('router._flush_done', 'flush: done', returncode=11)
```

### platform/shell/module/router/router/internal/_init_router.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

from shell.module.router.router_base.router_base import RouterBase

if TYPE_CHECKING:
    from shell.module.router.router.router import Router


def _init_router(router: 'Router') -> None:
    router.router_base_.init_router_base()
```

### platform/shell/module/router/router/internal/_parse_frontmatter.py
```
"""_parse_frontmatter.py
Responsible for one thing: parsing YAML front-matter from text.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import yaml


def _parse_frontmatter(text: str) -> Tuple[Optional[Dict], str]:
    """Parse YAML front-matter. Returns (data, body) or (None, text) on parse failure."""
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end == -1:
        return None, text
    fm_text = text[3:end].strip()
    body = text[end + 4:]
    try:
        data = yaml.safe_load(fm_text)
        return data, body
    except yaml.YAMLError:
        return None, text
```

### platform/shell/module/router/router/internal/_pick_active_file.py
```
from __future__ import annotations

from shell.utils.path.path import PathType


from shell.module.router.router.parse_message_filename import parse_message_filename
from shell.constants.constants import DIR_STAGE_ACTIVE


def _pick_active_file(app, node_stage) -> PathType | None:
    active_dir = node_stage.stage_dir_ / DIR_STAGE_ACTIVE
    app.app_trace_.record_info('router._pick_active_file', f'scanning: {active_dir}')
    active_files = node_stage.get_active_files()
    app.app_trace_.record_info(
        'router._pick_active_file',
        f'active_candidates={len(active_files)}'
    )
    if not active_files:
        return None
    picked = active_files[0]
    app.app_trace_.record_info(
        'router._pick_active_file',
        f'picked: {picked.name}'
    )
    return picked
```

### platform/shell/module/router/router/internal/_pick_agent_output.py
```
from __future__ import annotations


from shell.module.router.router.parse_message_filename import parse_message_filename
from shell.module.router.router.internal._assert_graph_node_role_set import _assert_graph_node_role_set
from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE, DIR_OUTPUT


def _message_id_sort_key(filename: str) -> int:
    parsed = parse_message_filename(filename)
    if parsed is None:
        return -1
    try:
        return int(parsed.message_id)
    except ValueError:
        return -1


def _pick_agent_output(app, agent_nodes) -> tuple[PathType, str] | None:
    all_candidates = []
    for graph_node in agent_nodes:
        agent_output_dir = graph_node.sub_node_properties_.node_dir_ / DOT_NODE / DIR_OUTPUT
        app.app_trace_.record_info('router._pick_agent_output', f'scanning: {agent_output_dir}')
        if not Path.exists(agent_output_dir):
            continue
        role = graph_node.role_
        _assert_graph_node_role_set(role, graph_node.node_name_)
        for f in Path.iterdir(agent_output_dir):
            if Path.is_file(f):
                all_candidates.append((f, role))
    app.app_trace_.record_info(
        'router._pick_agent_output',
        f'candidates={len(all_candidates)}'
    )
    if not all_candidates:
        return None
    all_candidates.sort(key=lambda pair: _message_id_sort_key(pair[0].name))
    picked_file, source_role = all_candidates[0]
    app.app_trace_.record_info(
        'router._pick_agent_output',
        f'picked: {picked_file.name} from role={source_role}'
    )
    return picked_file, source_role
```

### platform/shell/module/router/router/internal/_pick_parent_input.py
```
from __future__ import annotations


from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE, DIR_INPUT


def _pick_parent_input(app) -> PathType | None:
    parent_node_dir = app.cli_.cli_properties_.parent_node_dir_
    if parent_node_dir is None:
        return None
    input_dir = parent_node_dir / DOT_NODE / DIR_INPUT
    app.app_trace_.record_info('router._pick_parent_input', f'scanning: {input_dir}')
    if not Path.exists(input_dir):
        return None
    files = sorted([f for f in Path.iterdir(input_dir) if Path.is_file(f)])
    if not files:
        return None
    app.app_trace_.record_info('router._pick_parent_input', f'picked: {files[0].name}')
    return files[0]
```

### platform/shell/module/router/router/internal/_rename_parent_input_as_task.py
```
from __future__ import annotations

from shell.utils.path.path import PathType


from shell.module.router.router.parse_message_filename import SEPARATOR
from shell.module.router.router.parse_message_filename import parse_message_filename


def _rename_parent_input_as_task(parent_file: PathType, app, first_role: str, own_role: str) -> PathType:
    message_id = app.cli_.cli_properties_.message_id_
    thread_id = app.cli_.cli_properties_.thread_id_
    parsed = parse_message_filename(parent_file.name)
    intent = parsed.intent if parsed is not None else parent_file.stem
    suffix = parent_file.suffix
    new_name = SEPARATOR.join([
        '1', own_role, first_role, 'TASK', intent, thread_id, message_id, '1'
    ]) + suffix
    new_path = parent_file.parent / new_name
    parent_file.rename(new_path)
    return new_path
```

### platform/shell/module/router/router/internal/_route_incoming.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

from shell.module.router.router.parse_message_filename import FROM_PLACEHOLDER
from shell.module.router.router.parse_message_filename import build_message_filename
from shell.module.router.router.parse_message_filename import parse_message_filename
from shell.module.router.router.internal._assert_step_within_ttl import _assert_step_within_ttl
from shell.module.router.router.internal._distribute_active import _distribute_active
from shell.module.router.router_stage.internal._match_pending import _match_pending
from shell.utils.path.path import Path, PathType

if TYPE_CHECKING:
    from shell.module.router.router.router import Router


def _route_incoming(router: 'Router', node_stage, graph_nodes, picked_file: PathType, source_role: str, app) -> None:
    max_step = app.cli_.cli_properties_.max_step_

    parsed = parse_message_filename(picked_file.name)
    if parsed is not None:
        _assert_step_within_ttl(parsed, max_step)
    if parsed is not None and parsed.from_role == FROM_PLACEHOLDER:
        dest_name = build_message_filename(parsed, from_role=source_role)
    else:
        dest_name = picked_file.name

    app.app_trace_.record_info(
        'router._route_incoming',
        f'routing: {picked_file.name} msg_type={parsed.msg_type if parsed else None} to_role={parsed.to_role if parsed else None}'
    )

    if parsed is not None and parsed.msg_type == 'DONE':
        app.app_trace_.record_info('router._route_incoming', f'DONE received: {picked_file.name}')
        node_stage.save_to_done(picked_file)
        Path.unlink(picked_file)
        return

    if parsed is not None and parsed.to_role == 'router':
        matched_pending = _match_pending(node_stage, parsed)
        if matched_pending is not None:
            app.app_trace_.record_info('router._route_incoming', f'matched pending: {matched_pending.name}')
            node_stage.move_pending_to_history(matched_pending.name)
        app.app_trace_.record_info('router._route_incoming', f'saving to history: {picked_file.name}')
        node_stage.save_to_history(picked_file)
        Path.unlink(picked_file)
        return

    app.app_trace_.record_info('router._route_incoming', f'saving to active: {dest_name}')
    if picked_file.parent.name != 'active':
        node_stage.save_to_active(picked_file, dest_name=dest_name)
        Path.unlink(picked_file)
    _distribute_active(router, node_stage, graph_nodes, app)
```

### platform/shell/module/router/router/internal/_run_router.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

from shell.module.router.router.parse_message_filename import parse_message_filename
from shell.module.router.router.internal._expire_pending_ttl import _expire_pending_ttl
from shell.module.router.router.internal._flush_done import _flush_done
from shell.module.router.router.internal._pick_agent_output import _pick_agent_output
from shell.module.router.router.internal._assert_active_file_parsed import _assert_active_file_parsed
from shell.module.router.router.internal._pick_active_file import _pick_active_file
from shell.module.router.router.internal._pick_parent_input import _pick_parent_input
from shell.module.router.router.internal._rename_parent_input_as_task import _rename_parent_input_as_task
from shell.module.router.router.internal._route_incoming import _route_incoming
from shell.module.router.router.internal._seed_tasker_input_to_first_agent import _seed_tasker_input_to_first_agent

if TYPE_CHECKING:
    from shell.module.router.router.router import Router


def _run_router(router: 'Router') -> None:
    app = router._app
    max_step = app.cli_.cli_properties_.max_step_
    node_stage = router.router_stage_.node_stage_

    graph_nodes = router.router_base_.graph_nodes_
    non_router_nodes = [pn for pn in graph_nodes if pn.mode_ != 'router']

    _expire_pending_ttl(app, node_stage, max_step)

    agent_result = _pick_agent_output(app, non_router_nodes)
    active_file = _pick_active_file(app, node_stage)
    parent_input_file = _pick_parent_input(app)
    app.app_trace_.record_info('router._run_router', f'agent_result={agent_result[0].name if agent_result else None}')
    app.app_trace_.record_info('router._run_router', f'active_file={active_file.name if active_file else None}')
    app.app_trace_.record_info('router._run_router', f'parent_input_file={parent_input_file.name if parent_input_file else None}')

    if agent_result is not None:
        picked_file, source_role = agent_result
    elif active_file is not None:
        _parsed = parse_message_filename(active_file.name)
        _assert_active_file_parsed(_parsed, active_file)
        picked_file, source_role = active_file, _parsed.from_role
        app.app_trace_.record_info(
            'router._run_router',
            f'routing from active: {active_file.name} from_role={source_role}'
        )
    elif parent_input_file is not None:
        if not non_router_nodes:
            app.app_trace_.record_info('router._run_router', 'parent input found but no target nodes — skipping')
            return
        first_role = non_router_nodes[0].role_
        role = app.cli_.cli_properties_.role_
        renamed = _rename_parent_input_as_task(parent_input_file, app, first_role, role)
        picked_file, source_role = renamed, role
        app.app_trace_.record_info(
            'router._run_router',
            f'routing parent input as TASK: {renamed.name} to_role={first_role}'
        )
    else:
        if not node_stage.get_active_files():
            _flush_done(app, node_stage)
        return

    _route_incoming(router, node_stage, graph_nodes, picked_file, source_role, app)

```

### platform/shell/module/router/router/internal/_seed_tasker_input_to_first_agent.py
```
from __future__ import annotations


from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE, DIR_INPUT


def _seed_tasker_input_to_first_agent(app, agent_nodes) -> bool:
    task_dir = app.cli_.cli_properties_.task_dir_
    if task_dir is None:
        return False
    tasker_input_dir = task_dir.parent / DIR_INPUT
    if not Path.exists(tasker_input_dir):
        return False
    files = [f for f in Path.iterdir(tasker_input_dir) if Path.is_file(f)]
    if not files:
        return False
    if not agent_nodes:
        return False
    first_agent_input = agent_nodes[0].sub_node_properties_.node_dir_ / DOT_NODE / DIR_INPUT
    Path.mkdir(first_agent_input)
    for f in files:
        dest = first_agent_input / f.name
        Path.move(f, dest)
        app.app_trace_.record_info(
            'router._seed_tasker_input_to_first_agent',
            f'moved {f.name} from tasker input to {agent_nodes[0].node_name_} input'
        )
    return True
```

### platform/shell/module/router/router/load_router_params.py
```
"""load_router_params.py — DEPRECATED.
Use app.runner_.router_.init_router() instead.
"""


def load_router_params(app) -> None:
    """Deprecated. Delegates to app.runner_.router_.init_router()."""
    app.runner_.router_.init_router()

```

### platform/shell/module/router/router/parse_message_filename.py
```
from __future__ import annotations

from shell.utils.path.path import Path, PathType
from dataclasses import dataclass

SEPARATOR = '__'
FROM_PLACEHOLDER = 'X'


@dataclass
class MessageFilename:
    sequence_id: str
    from_role: str
    to_role: str
    msg_type: str
    intent: str
    thread_id: str
    message_id: str
    step: str
    suffix: str


def parse_message_filename(filename: str) -> MessageFilename | None:
    path = Path.new(filename)
    parts = path.stem.split(SEPARATOR)
    if len(parts) != 8:
        return None
    return MessageFilename(
        sequence_id=parts[0],
        from_role=parts[1],
        to_role=parts[2],
        msg_type=parts[3],
        intent=parts[4],
        thread_id=parts[5],
        message_id=parts[6],
        step=parts[7],
        suffix=path.suffix,
    )


def build_message_filename(parsed: MessageFilename, from_role: str) -> str:
    return SEPARATOR.join([
        parsed.sequence_id,
        from_role,
        parsed.to_role,
        parsed.msg_type,
        parsed.intent,
        parsed.thread_id,
        parsed.message_id,
        parsed.step,
    ]) + parsed.suffix


def increment_step(parsed: MessageFilename) -> str:
    try:
        new_step = str(int(parsed.step) + 1)
    except ValueError:
        new_step = parsed.step
    return SEPARATOR.join([
        parsed.sequence_id,
        parsed.from_role,
        parsed.to_role,
        parsed.msg_type,
        parsed.intent,
        parsed.thread_id,
        parsed.message_id,
        new_step,
    ]) + parsed.suffix
```

### platform/shell/module/router/router/read_metadata_from_file.py
```
from __future__ import annotations

from shell.utils.path.path import PathType

from collections.abc import Callable

from shell.module.router.router.internal._parse_frontmatter import _parse_frontmatter

from shell.utils.io.io import default_read_utf8


def read_metadata_from_file(
    path: PathType,
    reader: Callable[[PathType], str] | None = None,
) -> dict:
    """Return parsed frontmatter metadata from file. Empty dict if none.

    reader: optional callable (path: PathType) -> str for testability.
    """
    if reader is None:
        reader = default_read_utf8
    text = reader(path)
    data, _ = _parse_frontmatter(text)
    return data or {}
```

### platform/shell/module/router/router/router.py
```
"""router.py
Router: single entry point for all router-phase operations.

Delegates graph state (node order, role map, neighbours) to RouterBase.
Exposes domain-aware methods matching the router phase steps:

    move_prev_output_to_input()  — move previous node output/ → own input/
    copy_input_to_output()       — copy own input/ → own output/, prepend frontmatter
    distribute_output_to_targets() — fan-out own output/ to target nodes' input/

Query helpers (return values, never mutate app):
    get_next_graph_node()          — node after current in graph (or None)
    get_prev_graph_node()          — node before current in graph
    get_prev_graph_node_role()     — role of previous node
    get_prev_graph_node_output_dir() — Path to prev node output/
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from shell.utils.io.io import default_read_utf8, default_write_utf8
from shell.module.router.router.build_frontmatter import build_frontmatter
from shell.module.router.router.collect_source_files import collect_source_files
from shell.module.router.router.parse_message_filename import increment_step
from shell.module.router.router.parse_message_filename import parse_message_filename
from shell.module.router.router.internal._assert_role_set import _assert_role_set
from shell.module.router.router.internal._init_router import _init_router
from shell.module.router.router.internal._run_router import _run_router
from shell.module.router.router_base.router_base import RouterBase
from shell.module.router.router_stage.router_stage import RouterStage
from shell.utils.path.path import Path, PathType


class Router:
    """Router for a single node run.

    Resolves graph, role map and neighbour nodes once on construction.
    All IO methods accept injectable callables for full testability.
    """

    __slots__ = ("_app", "_router_base", "_router_stage")

    def __init__(self, app) -> None:
        self._app = app
        self._router_base: RouterBase | None = None
        self._router_stage: RouterStage | None = None

    @property
    def router_base_(self) -> RouterBase:
        if self._router_base is None:
            self._router_base = RouterBase(self._app)
        return self._router_base

    @property
    def router_stage_(self) -> RouterStage:
        if self._router_stage is None:
            self._router_stage = RouterStage(self._app)
        return self._router_stage

    # ------------------------------------------------------------------ #
    # Query helpers                                                        #
    # ------------------------------------------------------------------ #

    def get_next_graph_node(self) -> dict | None:
        return self.router_base_.get_next_graph_node(self._app.app_node_.node_.node_name_)

    def get_prev_graph_node(self) -> dict | None:
        return self.router_base_.get_prev_graph_node(self._app.app_node_.node_.node_name_)

    def get_prev_graph_node_role(self) -> str:
        """Return the role of the previous node.

        Raises ValueError if 'role' is missing.
        """
        node = self.get_prev_graph_node()
        role = node.get("role")
        _assert_role_set(role, node)
        return role

    def get_prev_graph_node_output_dir(self, resolve: bool = True) -> PathType:
        """Return the output/ directory of the previous node.

        resolve: when True (default) returns resolved absolute Path.
        """
        p = self._app.app_node_.node_.node_dir_.parent / self.get_prev_graph_node().node_name_ / ".node" / "output"
        return p.resolve() if resolve else p

    # ------------------------------------------------------------------ #
    # IO methods                                                           #
    # ------------------------------------------------------------------ #

    # deprecated
    def move_prev_output_to_input(
        self,
        copier: Callable[[PathType, Path], None] | None = None,
    ) -> list[str]:
        """Move previous node output/ to own input/.

        Returns list of moved filenames. Empty list if nothing to move.
        copier: optional callable (src: PathType, dst: PathType) -> None for testability.
        """
        if copier is None:
            copier = lambda src, dst: PathType.move(src, dst)

        src_dir = self.get_prev_graph_node_output_dir()
        dest_dir = self._app.app_node_.node_.node_dir_ / ".node" / "input"
        files = collect_source_files(src_dir)
        for f in files:
            copier(f, dest_dir / f.name)
        return [f.name for f in files]

    # deprecated
    def copy_input_to_output(
        self,
        timestamp: str | None = None,
        reader: Callable[[PathType], str] | None = None,
        writer: Callable[[PathType, str], None] | None = None,
    ) -> list[str]:
        """Copy own input/ to own output/, prepending YAML frontmatter.

        Frontmatter fields: source, target, timestamp, task_id.
        Returns list of copied filenames.
        reader: optional callable (path: PathType) -> str for testability.
        writer: optional callable (path: PathType, content: str) -> None for testability.
        """
        if reader is None:
            reader = default_read_utf8
        if writer is None:
            writer = default_write_utf8

        input_dir = self._app.app_node_.node_.node_dir_ / ".node" / "input"
        output_dir = self._app.app_node_.node_.node_dir_ / ".node" / "output"

        files = collect_source_files(input_dir)
        if not files:
            return []

        source_role = self.get_prev_graph_node_role()
        node_name = self._app.app_node_.node_.node_name_
        ts = timestamp or datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        copied = []
        for f in files:
            parsed = parse_message_filename(f.name)
            target_role = parsed.to_role if parsed is not None else ""
            content = build_frontmatter(reader(f), source_role, target_role, ts, node_name)
            writer(output_dir / f.name, content)
            copied.append(f.name)
        return copied

    # deprecated
    def distribute_output_to_targets(
        self,
        copier: Callable[[PathType, Path], None] | None = None,
    ) -> list[str]:
        """Fan-out own output/ to target nodes' input/ based on filename metadata.

        Target resolved from 'to' field in message filename format.
        Files with no resolvable target are skipped.
        Returns list of distributed filenames.
        copier: optional callable (src: PathType, dst: PathType) -> None for testability.
        """
        if copier is None:
            copier = Path.copy_to

        output_dir = self._app.app_node_.node_.node_dir_ / ".node" / "output"

        files = collect_source_files(output_dir)
        distributed = []

        next_node = self.get_next_graph_node()
        for f in files:
            parsed = parse_message_filename(f.name)
            target_role = parsed.to_role if parsed is not None else None
            target_node = (
                self.router_base_.role_to_node_map_.get(target_role) if target_role
                else next_node
            )
            if target_node is None:
                continue
            dest_name = increment_step(parsed) if parsed is not None else f.name
            dest_dir = self._app.app_node_.node_.node_dir_.parent / target_node.node_name_ / ".node" / "input"
            Path.mkdir(dest_dir)
            copier(f, dest_dir / dest_name)
            distributed.append(dest_name)

        return distributed

    # ------------------------------------------------------------------ #
    # Init                                                                 #
    # ------------------------------------------------------------------ #

    def init_router(self) -> None:
        _init_router(self)

    def run_router(self) -> None:
        """Execute the full router graph: copy input, build output, distribute."""
        _run_router(self)

    # ------------------------------------------------------------------ #
    # Private                                                              #
    # ------------------------------------------------------------------ #

    def _current_node_index(self) -> int:
        return self.router_base_.get_current_graph_node_index(self._app.app_node_.node_.node_name_)
```

### platform/shell/module/router/router_base/__init__.py
```
# router_base package
from shell.module.router.router_base.router_base import RouterBase
```

### platform/shell/module/router/router_base/internal/__init__.py
```
# router_maker internal package
```

### platform/shell/module/router/router_base/internal/_assert_node_in_graph.py
```
def _assert_node_in_graph(index, node_name: str) -> None:
    if index is None:
        raise ValueError(f"node '{node_name}' not found in graph")
```

### platform/shell/module/router/router_base/internal/_assert_task_md_file_body_set.py
```
def _assert_task_md_file_body_set(value) -> None:
    if value is None:
        raise ValueError("task_md_file_body not loaded — call init_router_base() first")
```

### platform/shell/module/router/router_base/internal/_assert_task_yaml_file_body_set.py
```
def _assert_task_yaml_file_body_set(value) -> None:
    if value is None:
        raise ValueError("task_yaml_file_body not loaded — call init_router_base() first")
```

### platform/shell/module/router/router_base/internal/_assert_task_yaml_in_task_dir.py
```
from __future__ import annotations

from shell.utils.path.path import PathType



def _assert_task_yaml_in_task_dir(yaml_files: list, task_dir: PathType) -> None:
    if not yaml_files:
        raise FileNotFoundError(f"[RouterBase] no .yaml file found in task_dir: {task_dir}")
```

### platform/shell/module/router/router_base/internal/_init_router_base.py
```
from __future__ import annotations

from shell.module.router.router_base.internal._assert_task_yaml_file_body_set import _assert_task_yaml_file_body_set
from shell.module.router.router_base.internal._assert_task_yaml_in_task_dir import _assert_task_yaml_in_task_dir
from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_TASK


def _init_router_base(router_base, reader=None) -> None:
    task_dir = (router_base._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TASK).resolve()
    yaml_files = Path.glob(task_dir, '*.yaml')
    _assert_task_yaml_in_task_dir(yaml_files, task_dir)
    task_yaml_file_body = Path.read_text(yaml_files[0])
    _assert_task_yaml_file_body_set(task_yaml_file_body)
    router_base._app.app_node_.node_.node_task_._task_yaml_file_body = task_yaml_file_body
    router_base._app.app_node_.node_.node_task_._task_name = yaml_files[0].stem
    router_base.graph_.init_graph()
```

### platform/shell/module/router/router_base/router_base.py
```
"""router_base.py
RouterBase: holds task files loaded from .node/task for every router node.

Slots:
    _app                 — parent App (back-reference)
    _graph            — Optional; lazy Graph instance
    _role_to_node_map    — dict[role, node] built from graph (dict | None)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.structure.graph.graph.graph import Graph
from shell.module.router.router_base.internal._assert_node_in_graph import _assert_node_in_graph
from shell.module.router.router_base.internal._init_router_base import _init_router_base


class RouterBase:
    """Holds task files and graph state for any router node."""

    __slots__ = ("_app", "_graph", "_role_to_node_map")

    def __init__(self, app=None) -> None:
        self._app = app
        self._graph = None
        self._role_to_node_map: dict | None = None
    @property
    def graph_(self) -> Graph:
        if self._graph is None:
            self._graph = Graph(self._app)
        return self._graph

    @property
    def graph_nodes_(self):
        return self.graph_.sub_nodes_

    @property
    def role_to_node_map_(self) -> dict:
        if self._role_to_node_map is None:
            self._role_to_node_map = {n.role_: n for n in self.graph_nodes_ if n.role_}
        return self._role_to_node_map

    def get_current_graph_node_index(self, node_name: str) -> int:
        index = next(
            (i for i, n in enumerate(self.graph_nodes_) if n.node_name_ == node_name),
            None,
        )
        _assert_node_in_graph(index, node_name)
        return index

    def get_next_graph_node(self, node_name: str):
        index = self.get_current_graph_node_index(node_name)
        graph_nodes = self.graph_nodes_
        return graph_nodes[index + 1] if index + 1 < len(graph_nodes) else None

    def get_prev_graph_node(self, node_name: str):
        index = self.get_current_graph_node_index(node_name)
        return self.graph_nodes_[index - 1] if index > 0 else None

    def init_router_base(self, reader=None) -> None:
        _init_router_base(self, reader=reader)
```

### platform/shell/module/router/router_stage/__init__.py
```
```

### platform/shell/module/router/router_stage/internal/__init__.py
```
```

### platform/shell/module/router/router_stage/internal/_match_pending.py
```
from __future__ import annotations

from shell.utils.path.path import PathType

from typing import TYPE_CHECKING

from shell.module.router.router.parse_message_filename import parse_message_filename

if TYPE_CHECKING:
    from shell.structure.node.node_stage.node_stage import NodeStage


def _match_pending(node_stage: 'NodeStage', parsed) -> PathType | None:
    if parsed is None or not parsed.thread_id:
        return None
    for pending_file in node_stage.get_pending_files():
        pending_parsed = parse_message_filename(pending_file.name)
        if pending_parsed is not None and pending_parsed.message_id == parsed.message_id:
            return pending_file
    return None
```

### platform/shell/module/router/router_stage/router_stage.py
```
"""router_stage.py
RouterStage — high-level stage management logic for the router node.

Slots:
    _app — parent App (DOM back-reference)

Delegates all physical I/O to NodeStage via app.app_node_.node_.node_stage_.
"""

from __future__ import annotations

from shell.utils.path.path import PathType


from shell.structure.node.node_stage.node_stage import NodeStage


class RouterStage:
    """High-level stage logic for the router — delegates physical I/O to NodeStage."""

    __slots__ = ("_app",)

    def __init__(self, app) -> None:
        self._app = app

    @property
    def node_stage_(self) -> NodeStage:
        return self._app.app_node_.node_.node_stage_
```

### platform/shell/module/tasker/__init__.py
```
```

### platform/shell/module/tasker/internal/__init__.py
```
```

### platform/shell/module/tasker/internal/_assert_first_non_router_node_exists.py
```
from __future__ import annotations


def _assert_first_non_router_node_exists(first_node) -> None:
    if first_node is None:
        raise ValueError("Graph has no non-router node — cannot seed task")
```

### platform/shell/module/tasker/internal/_assert_router_node_exists.py
```
def _assert_router_node_exists(router_node) -> None:
    if router_node is None:
        raise ValueError(
            "Graph configuration error: no router node (mode='router', role != 'maker') found in graph"
        )
```

### platform/shell/module/tasker/internal/_assert_session_id_set.py
```
def _assert_session_id_set(session_id: str | None) -> None:
    if session_id is None:
        raise RuntimeError('session_id is not set — call _init_task_yaml before accessing session_id_')
```

### platform/shell/module/tasker/internal/_assert_task_files_exist.py
```

from __future__ import annotations

from shell.utils.path.path import PathType




def _assert_task_files_exist(task_dir: PathType, task_files: list) -> None:
    if not task_files:
        raise FileNotFoundError(f"No *.md files found in task_dir: {task_dir}")
```

### platform/shell/module/tasker/internal/_assert_task_graph_yaml_exists.py
```
"""_assert_task_graph_yaml_exists.py
Responsible for one thing: raising FileNotFoundError when the task graph YAML file is missing.
"""

from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_task_graph_yaml_exists(path: PathType) -> None:
    if not Path.is_file(path):
        raise FileNotFoundError(f"[_validate_task] Task graph YAML not found: {path}")
```

### platform/shell/module/tasker/internal/_assert_task_graph_yaml_valid.py
```
"""_assert_task_graph_yaml_valid.py
Responsible for one thing: validating the structure of a loaded graph YAML dict.
"""

from __future__ import annotations


def _assert_task_graph_yaml_valid(data: dict) -> None:
    """Raise ValueError when graph YAML is missing required keys or structure."""
    if not isinstance(data, dict):
        raise ValueError(f"Graph YAML must be a mapping, got {type(data).__name__}")
    if 'graph' not in data:
        raise ValueError("Graph YAML is missing required key: 'graph'")
    if not isinstance(data['graph'], list):
        raise ValueError(f"Graph YAML 'graph' must be a list, got {type(data['graph']).__name__}")
    if not data['graph']:
        raise ValueError("Graph YAML 'graph' list must not be empty")
    for i, node in enumerate(data['graph']):
        for required in ('node_name', 'runner_root_dir', 'role', 'type'):
            if required not in node:
                raise ValueError(f"Graph node [{i}] is missing required key: '{required}'")
```

### platform/shell/module/tasker/internal/_assert_task_md_exists.py
```
"""_assert_task_md_exists.py
Responsible for one thing: raising FileNotFoundError when the task markdown file is missing.
"""

from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_task_md_exists(path: PathType) -> None:
    if not Path.is_file(path):
        raise FileNotFoundError(f"[_init_task_md] Task md not found: {path}")
```

### platform/shell/module/tasker/internal/_find_node_with_input.py
```
from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_INPUT


def _find_node_with_input(non_router_nodes) -> object | None:
    for pn in non_router_nodes:
        input_dir = pn.sub_node_properties_.node_dir_ / DOT_NODE / DIR_INPUT
        if Path.exists(input_dir) and any(Path.iterdir(input_dir)):
            return pn
    return None
```

### platform/shell/module/tasker/internal/_has_own_input.py
```
from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_INPUT


def _has_own_input(app) -> bool:
    input_dir = app.app_node_.node_.node_dir_ / DOT_NODE / DIR_INPUT
    return Path.exists(input_dir) and any(Path.iterdir(input_dir))
```

### platform/shell/module/tasker/internal/_has_own_output.py
```
from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_OUTPUT


def _has_own_output(app) -> bool:
    output_dir = app.app_node_.node_.node_dir_ / DOT_NODE / DIR_OUTPUT
    return Path.exists(output_dir) and any(Path.iterdir(output_dir))
```

### platform/shell/module/tasker/internal/_has_router_work.py
```
from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_OUTPUT


def _has_router_work(non_router_nodes, router_node) -> bool:
    for pn in non_router_nodes:
        output_dir = pn.sub_node_properties_.node_dir_ / DOT_NODE / DIR_OUTPUT
        if Path.exists(output_dir) and any(Path.iterdir(output_dir)):
            return True
    node_stage = router_node.sub_node_properties_.sub_node_node_stage_
    if node_stage.get_active_files():
        return True
    if node_stage.get_pending_files():
        return True
    return False
```

### platform/shell/module/tasker/internal/_init_new_node_statuses.py
```
from __future__ import annotations

import yaml

from shell.status.status import Status
from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_TASK


def _init_new_node_statuses(tasker) -> None:
    app = tasker._app
    task_dir = (app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TASK).resolve()
    yaml_files = Path.glob(task_dir, '*.yaml')
    if not yaml_files:
        return
    yaml_path = yaml_files[0]

    initialized_nodes = [pn for pn in tasker.graph_.sub_nodes_ if pn.status_ == Status.INITIALIZED]
    if not initialized_nodes:
        return

    data = yaml.safe_load(Path.read_text(yaml_path)) or {}
    for graph_node in initialized_nodes:
        for node_dict in data.get('graph', []):
            if node_dict.get('node_name') == graph_node.node_name_:
                node_dict['status'] = Status.INITIALIZED.name
                break

    Path.write_text(yaml_path, yaml.dump(data, default_flow_style=False, allow_unicode=True))
    app.app_trace_.record_info(
        'tasker._init_new_node_statuses._init_new_node_statuses',
        f'persisted INITIALIZED for {len(initialized_nodes)} new node(s) to {yaml_path.name}'
    )
```

### platform/shell/module/tasker/internal/_init_task_md.py
```
from __future__ import annotations

from collections.abc import Callable

from shell.utils.io.io import default_read_utf8
from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE, DIR_TASK


def _init_task_md(
    app,
    reader: Callable[[PathType], str] | None = None,
) -> None:
    if reader is None:
        reader = default_read_utf8

    task_dir = (app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TASK).resolve()
    task_name = app.cli_.cli_properties_.task_name_
    task_md_path = task_dir / f"{task_name}.md"

    if not Path.is_file(task_md_path):
        source_dir = Path.new(app.cli_.cli_properties_.source_dir_)
        source_md = source_dir / f"{task_name}.md"
        Path.copy_to(source_md, task_md_path)
        app.app_trace_.record_info('tasker._init_task_md._init_task_md', f'copy {source_md} -> {task_md_path}')

    app.runner_.tasker_._task_md_file_body = reader(task_md_path)
    app.app_trace_.record_info('tasker._init_task_md._init_task_md', f'read {task_md_path}')
```

### platform/shell/module/tasker/internal/_init_task_prompts.py
```
from __future__ import annotations


from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE, DIR_TASK


def _init_task_prompts(app) -> None:
    task_dir = (app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TASK).resolve()
    source_dir = Path.new(app.cli_.cli_properties_.source_dir_)

    for source_prompt in Path.glob(source_dir, '*.prompt.md'):
        dest = task_dir / source_prompt.name
        if not Path.is_file(dest):
            Path.copy_to(source_prompt, dest)
            app.app_trace_.record_info(
                'tasker._init_task_prompts._init_task_prompts',
                f'copy {source_prompt} -> {dest}'
            )
```

### platform/shell/module/tasker/internal/_init_task_yaml.py
```
from __future__ import annotations

import yaml
from collections.abc import Callable
from datetime import datetime

from shell.utils.io.io import default_read_utf8, default_write_utf8
from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE, DIR_TASK


def _init_task_yaml(
    app,
    reader: Callable[[PathType], str] | None = None,
    writer: Callable[[PathType, str], None] | None = None,
) -> None:
    if reader is None:
        reader = default_read_utf8
    if writer is None:
        writer = default_write_utf8

    task_dir = (app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TASK).resolve()
    task_name = app.cli_.cli_properties_.task_name_
    task_yaml_path = task_dir / f"{task_name}.yaml"

    if not Path.is_file(task_yaml_path):
        source_dir = Path.new(app.cli_.cli_properties_.source_dir_)
        source_yaml = source_dir / f"{task_name}.yaml"
        Path.copy_to(source_yaml, task_yaml_path)
        app.app_trace_.record_info('tasker._init_task_yaml._init_task_yaml', f'copy {source_yaml} -> {task_yaml_path}')

    app.runner_.tasker_._task_yaml_file_body = reader(task_yaml_path)
    app.app_trace_.record_info('tasker._init_task_yaml._init_task_yaml', f'read {task_yaml_path}')

    session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    app.runner_.tasker_._session_id = session_id

    data = yaml.safe_load(app.runner_.tasker_._task_yaml_file_body) or {}
    data['session_id'] = session_id
    writer(task_yaml_path, yaml.dump(data, default_flow_style=False, allow_unicode=True))
    app.app_trace_.record_info('tasker._init_task_yaml._init_task_yaml', f'session_id={session_id} written to {task_yaml_path}')
```

### platform/shell/module/tasker/internal/_init_tasker.py
```
from __future__ import annotations

from shell.module.tasker.internal._validate_task import _validate_task
from shell.module.tasker.internal._seed_graph_node_task import _seed_graph_node_task


def _init_tasker(tasker, reader=None) -> None:
    _validate_task(tasker._app)
    tasker.graph_.init_graph()
    _seed_graph_node_task(tasker)
```

### platform/shell/module/tasker/internal/_move_router_output_to_own.py
```
from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_OUTPUT


def _move_router_output_to_own(tasker, app) -> bool:
    sub_nodes = tasker.graph_.sub_nodes_
    router_nodes = [pn for pn in sub_nodes if pn.mode_ == 'router']
    if not router_nodes:
        return False
    router_output_dir = router_nodes[0].sub_node_properties_.node_dir_ / DOT_NODE / DIR_OUTPUT
    if not Path.exists(router_output_dir):
        return False
    files = [f for f in Path.iterdir(router_output_dir) if Path.is_file(f)]
    if not files:
        return False
    own_output_dir = app.app_node_.node_.node_dir_ / DOT_NODE / DIR_OUTPUT
    Path.mkdir(own_output_dir)
    for file in files:
        Path.move(file, own_output_dir / file.name)
    app.app_trace_.record_info('tasker._run_iterative_tasker', f'moved {len(files)} file(s) from router output to own output')
    return True
```

### platform/shell/module/tasker/internal/_run_iterative_tasker.py
```
from __future__ import annotations

from shell.structure.graph.graph.internal._persist_node_status import _persist_node_status
from shell.structure.sub_node.sub_node.internal._run_sub_node import _run_sub_node
from shell.status.status import Status
from shell.module.tasker.internal._seed_task_to_first_node import _seed_task_to_first_node
from shell.module.tasker.internal._find_node_with_input import _find_node_with_input
from shell.module.tasker.internal._has_router_work import _has_router_work
from shell.module.tasker.internal._has_own_output import _has_own_output
from shell.module.tasker.internal._has_own_input import _has_own_input
from shell.module.tasker.internal._move_router_output_to_own import _move_router_output_to_own
from shell.module.tasker.internal._init_task_md import _init_task_md
from shell.module.tasker.internal._init_task_yaml import _init_task_yaml
from shell.module.tasker.internal._init_task_prompts import _init_task_prompts
from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_INPUT, DIR_OUTPUT, DIR_TASK

_MAX_ITERATIONS = 200


def _run_iterative_tasker(tasker) -> Status:
    app = tasker._app
    task_dir = (app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TASK).resolve()

    if _has_own_output(app):
        app.app_trace_.record_info('tasker._run_iterative_tasker', 'own output not empty — skipping execution')
        return Status.SUCCESS

    if not _has_own_input(app):
        app.app_trace_.record_info('tasker._run_iterative_tasker', 'own input empty — skipping execution')
        return Status.SUCCESS


    iteration = 0
    # _seed_task_to_first_node(tasker, task_dir)

    _own_node_dir = app.app_node_.node_.node_dir_ / DOT_NODE
    _input_dir = _own_node_dir / DIR_INPUT
    _output_dir = _own_node_dir / DIR_OUTPUT
    _input_files = Path.iterdir(_input_dir) if Path.exists(_input_dir) else []
    _output_files = Path.iterdir(_output_dir) if Path.exists(_output_dir) else []
    app.app_trace_.record_info('tasker._run_iterative_tasker', f'input dir: {_input_dir} files: {[f.name for f in _input_files]}')
    app.app_trace_.record_info('tasker._run_iterative_tasker', f'output dir: {_output_dir} files: {[f.name for f in _output_files]}')

    while True:
        if iteration >= _MAX_ITERATIONS:
            raise RuntimeError(f"tasker stalled after {_MAX_ITERATIONS} iterations without reaching DONE")
        iteration += 1

        sub_nodes = tasker.graph_.sub_nodes_
        non_router_nodes = [pn for pn in sub_nodes if pn.mode_ != 'router']
        router_nodes = [pn for pn in sub_nodes if pn.mode_ == 'router']

        if _move_router_output_to_own(tasker, app):
            return Status.DONE

        node_with_input = _find_node_with_input(non_router_nodes)
        if node_with_input is not None:
            app.app_trace_.record_info('tasker._run_iterative_tasker', f"agent input found — running {node_with_input.node_name_}")
            status = _run_sub_node(node_with_input, task_dir, app)
            _persist_node_status(node_with_input, app)
            if status == Status.ERROR:
                return Status.ERROR
            continue

        if router_nodes:
            router_node = router_nodes[0]
            if _has_router_work(non_router_nodes, router_node):
                app.app_trace_.record_info('tasker._run_iterative_tasker', f"router work found — running {router_node.node_name_}")
                status = _run_sub_node(router_node, task_dir, app)
                _persist_node_status(router_node, app)
                if status == Status.ERROR:
                    return Status.ERROR
                if status == Status.DONE:
                    _move_router_output_to_own(tasker, app)
                    return Status.DONE
                continue

            if _has_own_input(app):
                app.app_trace_.record_info('tasker._run_iterative_tasker', f"own input not empty — running {router_node.node_name_}")
                status = _run_sub_node(router_node, task_dir, app)
                _persist_node_status(router_node, app)
                if status == Status.ERROR:
                    return Status.ERROR
                if status == Status.DONE:
                    _move_router_output_to_own(tasker, app)
                    return Status.DONE
                continue

            app.app_trace_.record_info('tasker._run_iterative_tasker', f"no work — flushing via {router_node.node_name_}")
            status = _run_sub_node(router_node, task_dir, app)
            _persist_node_status(router_node, app)
            if status == Status.ERROR:
                return Status.ERROR
            if status == Status.DONE:
                _move_router_output_to_own(tasker, app)
                return Status.DONE
            break

        break

    return Status.SUCCESS
```

### platform/shell/module/tasker/internal/_run_tasker.py
```
from __future__ import annotations

from shell.status.status import Status
from shell.module.tasker.internal._run_iterative_tasker import _run_iterative_tasker


def _run_tasker(tasker) -> Status:
    app = tasker._app
    app.app_trace_.record_info('tasker.Tasker.run_tasker', f"starting task {tasker.task_name_}")
    result = Status.SUCCESS
    try:
        result = _run_iterative_tasker(tasker)
    except Exception as exc:
        result = Status.ERROR
        app.app_trace_.record_error_and_raise('tasker.Tasker.run_tasker', Exception(f"task {tasker.task_name_} failed: {exc}"))
    app.app_trace_.record_info('tasker.Tasker.run_tasker', f"task {tasker.task_name_} completed status={result.name}({int(result)})")
    return result
```

### platform/shell/module/tasker/internal/_seed_graph_node_task.py
```
from __future__ import annotations

from shell.structure.graph.graph.internal._persist_node_status import _persist_node_status
from shell.status.status import Status
from shell.module.tasker.internal._assert_router_node_exists import _assert_router_node_exists
from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_TASK


def _seed_graph_node_task(tasker) -> None:
    app = tasker._app

    router_node = next(
        (pn for pn in tasker.graph_.sub_nodes_
         if pn.mode_ == 'router'
         and pn.role_ != 'maker'),
        None,
    )
    _assert_router_node_exists(router_node)

    router_node.node_status_.set_status(Status.READY)
    _persist_node_status(router_node, app)
    app.app_trace_.record_info(
        'tasker._seed_graph_node_task',
        f'node {router_node.node_name_} status=READY(8)'
    )

    node_task = app.app_node_.node_.node_task_
    task_name = node_task.task_name_
    task_md_file_body = node_task.task_md_file_body_
    if task_name is None or task_md_file_body is None:
        return

    task_dir = router_node.sub_node_properties_.node_dir_ / DOT_NODE / DIR_TASK
    Path.mkdir(task_dir)
    Path.write_text(task_dir / f'{task_name}.md', task_md_file_body)
    app.app_trace_.record_info(
        'tasker._seed_graph_node_task',
        f'seeded {task_name}.md into {router_node.node_name_} task'
    )
```

### platform/shell/module/tasker/internal/_seed_task_to_first_node.py
```
from __future__ import annotations

from shell.module.tasker.internal._assert_first_non_router_node_exists import _assert_first_non_router_node_exists
from shell.module.tasker.internal._assert_task_files_exist import _assert_task_files_exist
from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_INPUT


def _seed_task_to_first_node(tasker, task_dir) -> None:
    sub_nodes = tasker.graph_.sub_nodes_
    first_node = next((pn for pn in sub_nodes if pn.mode_ != 'router'), None)
    _assert_first_non_router_node_exists(first_node)
    task_files = Path.glob(task_dir, '*.md') if Path.exists(task_dir) else []
    _assert_task_files_exist(task_dir, task_files)
    input_dir = first_node.sub_node_properties_.node_dir_ / DOT_NODE / DIR_INPUT
    Path.mkdir(input_dir)
    for task_file in task_files:
        Path.copy_to(task_file, input_dir / task_file.name)
    tasker._app.app_trace_.record_info(
        'tasker._run_iterative_tasker._seed_task_to_first_node',
        f'seeded {len(task_files)} file(s) from task_dir to {first_node.node_name_} input'
    )
```

### platform/shell/module/tasker/internal/_validate_task.py
```
"""_validate_task.py
Responsible for one thing: asserting that all required task files exist.
"""

from __future__ import annotations

from shell.module.tasker.internal._assert_task_md_exists import _assert_task_md_exists
from shell.module.tasker.internal._assert_task_graph_yaml_exists import _assert_task_graph_yaml_exists
from shell.constants.constants import DOT_NODE, DIR_TASK


def _validate_task(app) -> None:
    """Assert that all required task files exist."""
    task_dir = (app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TASK).resolve()
    task_name = app.cli_.cli_properties_.task_name_
    _assert_task_graph_yaml_exists(task_dir / f"{task_name}.yaml")
    _assert_task_md_exists(task_dir / f"{task_name}.md")
```

### platform/shell/module/tasker/tasker.py
```
"""tasker.py
Tasker: structured runtime state for a single task.

Slots:
    _app         — parent App (DOM back-reference)
    _graph              — Graph instance (built by init_tasker)
    _session_id            — Optional; session timestamp string (YYYYmmdd_HHMMSS)

Validated properties:
    task_dir_              — resolved Path to node directory (task lives there)
    task_name_             — name derived from node directory name
"""

from __future__ import annotations
from shell.structure.graph.graph.graph import Graph
from shell.status.status import Status
from shell.module.tasker.internal._assert_session_id_set import _assert_session_id_set
from shell.module.tasker.internal._init_tasker import _init_tasker
from shell.module.tasker.internal._run_tasker import _run_tasker


class Tasker:
    """Structured task data for a shell graph run.

    Constructed lazily and held as app.runner_.tasker_.
    """

    __slots__ = ("_app", "_graph", "_session_id")

    def __init__(self, app) -> None:
        self._app = app
        self._graph: Graph | None = None
        self._session_id: str | None = None

    @property
    def graph_(self) -> Graph:
        """Return the cached Graph instance for this task."""
        if self._graph is None:
            self._graph = Graph(self._app)
        return self._graph

    @property
    def task_name_(self) -> str:
        """Name of the node directory on which this task is executed."""
        return self._app.app_node_.node_.node_dir_.name

    @property
    def session_id_(self) -> str:
        _assert_session_id_set(self._session_id)
        return self._session_id

    def init_tasker(self, reader=None) -> None:
        _init_tasker(self, reader=reader)

    def run_tasker(self) -> Status:
        return _run_tasker(self)
```

### platform/shell/module/tool/__init__.py
```
```

### platform/shell/module/tool/tool/__init__.py
```
from shell.module.tool.tool.tool import Tool
```

### platform/shell/module/tool/tool/internal/__init__.py
```
```

### platform/shell/module/tool/tool/internal/_init_tool.py
```
"""_init_tool.py
Delegate initialization to tool_properties and tool_command.
"""

from __future__ import annotations


def _init_tool(tool, reader=None) -> None:
    app = tool._app

    try:
        tool.tool_properties_.init_tool_properties()
    except ValueError as exc:
        app.app_trace_.record_error_and_raise('tool._init_tool._init_tool', exc)
```

### platform/shell/module/tool/tool/internal/_run_tool.py
```
from __future__ import annotations

import subprocess

from shell.component.process.process.process import Process
from shell.status.status import Status


def _run_tool(tool, runner=None) -> Status:
    app = tool._app
    process = Process(app, runner)
    process.init_process_tool()
    try:
        process.run_process()
        app.app_trace_.record_info(
            'tool._run_tool._run_tool',
            f'returncode={process.returncode_}',
            stdout=process.stdout_,
            stderr=process.stderr_,
            returncode=process.returncode_,
        )
        if process.stderr_:
            app.app_trace_.record_warning(
                'tool._run_tool._run_tool',
                Exception(f"stderr (returncode={process.returncode_}): {process.stderr_.strip()}"),
                stdout=process.stdout_,
                stderr=process.stderr_,
                returncode=process.returncode_,
            )
        return Status.from_returncode(process.returncode_)
    except subprocess.TimeoutExpired:
        return Status.from_returncode(2)
    except Exception as exc:
        app.app_trace_.record_error('tool._run_tool._run_tool', exc)
        return Status.from_returncode(1)
```

### platform/shell/module/tool/tool/tool.py
```
"""tool.py
Tool — wrapper for external tools in a graph node.

Tools are extra apps that do NOT generate working logs (unlike scripts/workers).

Responsibilities:
    init_tool()   — validate tool fields from node_config
    run_tool()    — build command, run subprocess, return Status
"""

from __future__ import annotations

from collections.abc import Callable
from subprocess import CompletedProcess

from shell.module.tool.tool.internal._init_tool import _init_tool
from shell.module.tool.tool.internal._run_tool import _run_tool
from shell.status.status import Status
from shell.module.tool.tool_properties.tool_properties import ToolProperties


class Tool:
    """Runs an external tool process for a single graph node."""

    __slots__ = ("_app", "_tool_properties")

    def __init__(self, app) -> None:
        self._app = app
        self._tool_properties: ToolProperties | None = None

    def init_tool(self, reader=None) -> None:
        _init_tool(self, reader=reader)

    def run_tool(
        self,
        runner: Callable[..., CompletedProcess] | None = None,
    ) -> Status:
        return _run_tool(self, runner=runner)

    @property
    def tool_properties_(self) -> ToolProperties:
        if self._tool_properties is None:
            self._tool_properties = ToolProperties(self._app)
        return self._tool_properties
```

### platform/shell/module/tool/tool_properties/__init__.py
```
```

### platform/shell/module/tool/tool_properties/tool_properties.py
```
"""tool_properties.py
ToolProperties — placeholder for future tool execution parameters.
"""

from __future__ import annotations


class ToolProperties:
    """Holds Tool runtime parameters extracted from YAML config."""

    __slots__ = ("_app",)

    def __init__(self, app) -> None:
        self._app = app

    def init_tool_properties(self) -> None:
        pass
```

### platform/shell/module/worker/__init__.py
```
from shell.module.worker.worker.worker import Worker
```

### platform/shell/module/worker/worker/__init__.py
```
from shell.module.worker.worker.worker import Worker

__all__ = ["Worker"]
```

### platform/shell/module/worker/worker/internal/__init__.py
```
```

### platform/shell/module/worker/worker/internal/_init_worker.py
```
"""_init_worker.py
Delegate initialization to worker_properties.
"""

from __future__ import annotations


def _init_worker(worker, reader=None) -> None:
    app = worker._app

    try:
        worker.worker_properties_.init_worker_properties()
    except ValueError as exc:
        app.app_trace_.record_error_and_raise('worker._init_worker._init_worker', exc)
```

### platform/shell/module/worker/worker/internal/_run_worker.py
```
"""_run_worker.py
Run the external script or process defined in worker.yaml.

Builds the subprocess command from WorkerConfig, runs it, captures output,
writes stdout to output/stdout.txt when capture includes stdout,
and returns Status based on returncode.
"""

from __future__ import annotations

import subprocess
import sys

from shell.status.status import Status


def _run_worker(worker, runner=None) -> Status:
    """Run the external process and return its Status.

    runner: optional callable with the same signature as subprocess.run (for testing).
    """
    if runner is None:
        runner = subprocess.run

    app = worker._app
    app_properties = app.app_properties_
    node_dir = app.app_node_.node_.node_dir_

    cmd = _build_cmd(app_properties)

    env = None

    try:
        proc = runner(
            cmd,
            capture_output=True,
            text=True,
            timeout=app_properties.timeout_,
            encoding='utf-8',
            errors='replace',
            cwd=node_dir,
            env=env,
        )
        app.app_trace_.record_info(
            'worker._run_worker._run_worker',
            f'returncode={proc.returncode}',
            stdout=proc.stdout,
            stderr=proc.stderr,
            returncode=proc.returncode,
        )
        if proc.stderr:
            app.app_trace_.record_warning(
                'worker._run_worker._run_worker',
                Exception(f"stderr (returncode={proc.returncode}): {proc.stderr.strip()}"),
                stdout=proc.stdout,
                stderr=proc.stderr,
                returncode=proc.returncode,
            )
        return Status.from_returncode(proc.returncode)
    except subprocess.TimeoutExpired as exc:
        partial_out = exc.output or ''
        partial_err = exc.stderr or f'Timeout after {app_properties.timeout_}s'
        app.app_trace_.record_warning_and_raise('worker._run_worker._run_worker', exc, stdout=partial_out, stderr=partial_err)
    except OSError as exc:
        app.app_trace_.record_error_and_raise('worker._run_worker._run_worker', exc)
    except Exception as exc:  # noqa: BLE001
        app.app_trace_.record_error_and_raise('worker._run_worker._run_worker', exc)


def _build_cmd(cfg) -> list[str]:
    if cfg.type_ == 'python_module':
        return [sys.executable, '-m', cfg.command_]
    return [cfg.command_]
```

### platform/shell/module/worker/worker/worker.py
```
"""worker.py
Worker — wrapper for external scripts and processes in a graph node.

Responsibilities:
    init_worker()   — validate worker fields from node_config
    run_worker()    — build command, run subprocess, return Status
"""

from __future__ import annotations

from collections.abc import Callable
from subprocess import CompletedProcess

from shell.module.worker.worker.internal._init_worker import _init_worker
from shell.module.worker.worker.internal._run_worker import _run_worker
from shell.status.status import Status
from shell.module.worker.worker_properties.worker_properties import WorkerProperties


class Worker:
    """Runs an external script or process for a single graph node."""

    __slots__ = ("_app", "_script_file_body", "_worker_properties")

    def __init__(self, app) -> None:
        self._app = app
        self._script_file_body: str | None = None
        self._worker_properties: WorkerProperties | None = None

    # -----------------------------------------------------------------------
    # Domain methods
    # -----------------------------------------------------------------------

    def init_worker(self, reader=None) -> None:
        """Validate worker fields from node_config."""
        _init_worker(self, reader=reader)

    def run_worker(
        self,
        runner: Callable[..., CompletedProcess] | None = None,
    ) -> Status:
        """Run the external process and return its Status."""
        return _run_worker(self, runner=runner)

    # -----------------------------------------------------------------------
    # Lazy properties
    # -----------------------------------------------------------------------

    @property
    def worker_properties_(self) -> WorkerProperties:
        """Return WorkerProperties, creating it on first access."""
        if self._worker_properties is None:
            self._worker_properties = WorkerProperties(self._app)
        return self._worker_properties
```

### platform/shell/module/worker/worker_properties/__init__.py
```
```

### platform/shell/module/worker/worker_properties/worker_properties.py
```
"""WorkerProperties — placeholder for future worker execution parameters."""

from __future__ import annotations

_VALID_TYPES: frozenset[str] = frozenset({'script', 'process', 'python_module'})


class WorkerProperties:
    """Holds Worker runtime parameters extracted from YAML config."""

    __slots__ = ("_app",)

    def __init__(self, app) -> None:
        self._app = app

    def init_worker_properties(self) -> None:
        app_properties = self._app.app_properties_
        if app_properties.type_ not in _VALID_TYPES:
            raise ValueError(
                f"Invalid worker type: {app_properties.type_!r}. Must be one of {sorted(_VALID_TYPES)}"
            )
        if not app_properties.command_:
            raise ValueError("config.yaml missing required field: 'command'")
```

### platform/shell/status/__init__.py
```
from shell.status.status import Status

__all__ = ["Status"]
```

### platform/shell/status/module_status/__init__.py
```
from shell.status.module_status.module_status import ModuleStatus
```

### platform/shell/status/module_status/module_status/__init__.py
```
from shell.status.module_status.module_status.module_status import ModuleStatus
```

### platform/shell/status/module_status/module_status/module_status.py
```
"""module_status.py
ModuleStatus — lifecycle status for node child modules.

Values:
    NEW   — initial; module constructed, not yet initialized
    INIT  — init method has been called successfully
"""

from __future__ import annotations

from enum import Enum


class ModuleStatus(Enum):
    NEW = 'new'
    INIT = 'init'
```

### platform/shell/status/status/__init__.py
```
from shell.status.status.status import Status
```

### platform/shell/status/status/status.py
```
"""status.py
Status — semantic result of a graph run.

Values match OS exit codes:
    SUCCESS  = 0
    ERROR    = 1
    TIMEOUT  = 2
    WARNING  = 3
    LOCKED   = 4
    QUESTION = 5
    WAITING  = 6
    SKIP     = 7
    READY        = 8
    INITIALIZED  = 9
    NULL         = 10
    DONE         = 11
    CRITICAL = 99
"""

from __future__ import annotations

from enum import Enum


class Status(int, Enum):
    SUCCESS = 0
    ERROR = 1
    TIMEOUT = 2
    WARNING = 3
    LOCKED = 4
    QUESTION = 5
    WAITING = 6
    SKIP = 7
    READY = 8
    INITIALIZED = 9
    NULL = 10
    DONE = 11
    CRITICAL = 99

    @classmethod
    def from_returncode(cls, returncode: int) -> 'Status':
        try:
            return cls(returncode)
        except ValueError:
            return cls.ERROR

    @classmethod
    def from_str(cls, value: str) -> 'Status':
        try:
            return cls[value.upper()]
        except KeyError:
            raise ValueError(f"[Status] Unknown status value: '{value}'")
```

### platform/shell/structure/__init__.py
```
```

### platform/shell/structure/graph/__init__.py
```
from shell.structure.graph.graph.graph import Graph
```

### platform/shell/structure/graph/graph/__init__.py
```
from shell.structure.graph.graph.graph import Graph
```

### platform/shell/structure/graph/graph/graph.py
```
from __future__ import annotations

from shell.structure.graph.graph.internal._init_graph import _init_graph
from shell.structure.sub_node.sub_node.sub_node import SubNode
from shell.status.status import Status


class Graph:
    """Graph nodes loaded from a task YAML.

    ``self.graph_nodes`` is an empty list until ``init_graph`` is called,
    at which point it is populated as ``list[SubNode]`` from ``task_graph_yaml``.

    Supports iteration, len, and indexing so it can be used directly
    wherever a sequence of graph nodes is expected.
    """

    __slots__ = ("_sub_nodes", "_app", "_status")

    def __init__(self, app=None) -> None:
        self._sub_nodes: list[SubNode] = []
        self._app = app
        self._status: Status = Status.NULL

    @property
    def status_(self) -> Status:
        return self._status

    # ------------------------------------------------------------------ #
    # Sequence protocol                                                    #
    # ------------------------------------------------------------------ #

    def __iter__(self):
        return iter(self._sub_nodes)

    def __len__(self) -> int:
        return len(self._sub_nodes)

    def __getitem__(self, index):
        return self._sub_nodes[index]

    # ------------------------------------------------------------------ #
    # Pure queries                                                         #
    # ------------------------------------------------------------------ #

    @property
    def sub_nodes_(self) -> list:
        return self._sub_nodes

    # ------------------------------------------------------------------ #
    # Mutating operations                                                  #
    # ------------------------------------------------------------------ #

    def init_graph(
        self,
        reader=None,
        writer=None,
    ) -> None:
        _init_graph(self, reader=reader, writer=writer)
```

### platform/shell/structure/graph/graph/internal/__init__.py
```
```

### platform/shell/structure/graph/graph/internal/_init_graph.py
```
"""_init_graph.py
Private. Load graph YAML from disk, validate and initialize graph_nodes.
"""

from __future__ import annotations

import yaml

from shell.utils.io.io import default_read_utf8, default_write_utf8
from shell.status.status import Status
from shell.structure.sub_node.sub_node.sub_node import SubNode
from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_TASK


def _init_graph(graph, reader=None, writer=None) -> None:
    if reader is None:
        reader = default_read_utf8
    if writer is None:
        writer = default_write_utf8

    task_graph_dict = graph._app.app_node_.node_.node_task_.task_graph_dict_
    task_dir = (graph._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TASK).resolve()

    sub_nodes = []
    for sub_node_dict in task_graph_dict['graph']:
        sub_node = SubNode(app=graph._app)
        sub_node.init_sub_node(sub_node_dict, writer=writer, reader=reader)
        sub_nodes.append(sub_node)
    graph._sub_nodes = sub_nodes

    task_name = graph._app.app_node_.node_.node_task_.task_name_
    yaml_path = task_dir / f'{task_name}.yaml'
    Path.write_text(yaml_path, yaml.dump(task_graph_dict, default_flow_style=False, allow_unicode=True))
    graph._app.app_trace_.record_info(
        'graph._init_graph._init_graph',
        f'persisted graph status to {yaml_path.name}'
    )
```

### platform/shell/structure/graph/graph/internal/_load_graph_yaml.py
```
from __future__ import annotations

import yaml

from shell.module.tasker.internal._assert_task_graph_yaml_valid import _assert_task_graph_yaml_valid


def _load_graph_yaml(graph) -> dict:
    task_yaml_file_body = graph._app.app_node_.node_.node_task_.task_yaml_file_body_
    graph_yaml = yaml.safe_load(task_yaml_file_body)
    _assert_task_graph_yaml_valid(graph_yaml)
    return graph_yaml
```

### platform/shell/structure/graph/graph/internal/_persist_node_status.py
```
from __future__ import annotations

import yaml

from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE, DIR_TASK


def _persist_node_status(sub_node, app) -> None:
    task_dir = (app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TASK).resolve()
    yaml_files = Path.glob(task_dir, '*.yaml')
    if not yaml_files:
        return
    yaml_path = yaml_files[0]
    data = yaml.safe_load(Path.read_text(yaml_path)) or {}
    for node_dict in data.get('graph', []):
        if node_dict.get('node_name') == sub_node.node_name_:
            node_dict['status'] = sub_node.status_.name
            break
    Path.write_text(yaml_path, yaml.dump(data, default_flow_style=False, allow_unicode=True))
    app.app_trace_.record_info(
        'graph._persist_node_status._persist_node_status',
        f'persisted status={sub_node.status_.name} for node {sub_node.node_name_} to {yaml_path.name}'
    )
```

### platform/shell/structure/graph/graph_status/graph_status.py
```
"""graph_status.py
GraphStatus — derives overall graph status from node statuses.

Slots:
    _graph    — parent Graph instance (back-reference)
    _app  — parent App instance (back-reference)

Validated properties:
    graph_status_  — overall Status derived from node statuses
"""

from __future__ import annotations
class Status(int, Enum):
    SUCCESS = 0
    ERROR = 1
    TIMEOUT = 2
    WARNING = 3
    LOCKED = 4
    QUESTION = 5
    WAITING = 6
    SKIP = 7
    READY = 8
    INITIALIZED = 9
    NULL = 10
    DONE = 11
    CRITICAL = 99tam gdzie uzywana 
from shell.status.status import Status

_STATUS_PRIORITY = (
    Status.ERROR,
    Status.LOCKED,
    Status.TIMEOUT,
    Status.WAITING,
    Status.QUESTION,
)
_SUCCESS_STATES = frozenset({Status.SUCCESS, Status.SKIP})


class GraphStatus:
    """Derives overall graph status from node statuses (priority order).

    Priority: ERROR > LOCKED > TIMEOUT > WAITING > QUESTION > SUCCESS.
    Returns Status.SUCCESS only when all nodes are in {SUCCESS, SKIP}.
    """

    __slots__ = ("_graph", "_app")

    def __init__(self, graph) -> None:
        self._graph = graph
        self._app = graph._app

    @property
    def graph_status_(self) -> Status:
        """Derive overall graph status from node statuses (priority order)."""
        sub_nodes = self._graph.sub_nodes_
        statuses = {n.node_.status_ for n in sub_nodes}
        for s in _STATUS_PRIORITY:
            if s in statuses:
                return s
        if all(n.node_.status_ in _SUCCESS_STATES for n in sub_nodes):
            return Status.SUCCESS
        for node in sub_nodes:
            if node.node_.status_ not in _SUCCESS_STATES:
                return node.node_.status_
        return Status.SUCCESS
```

### platform/shell/structure/node/__init__.py
```
from shell.structure.node.node.node import Node
```

### platform/shell/structure/node/node/__init__.py
```
from shell.structure.node.node.node import Node
```

### platform/shell/structure/node/node/internal/__init__.py
```
```

### platform/shell/structure/node/node/internal/_assert_config_yaml_exists.py
```
from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_config_yaml_exists(path: PathType) -> None:
    if not Path.is_file(path):
        raise FileNotFoundError(f"[_validate_node] Node config not found: {path}")
```

### platform/shell/structure/node/node/internal/_assert_input_dir_exists.py
```
"""_assert_input_dir_exists.py
Responsible for one thing: raising FileNotFoundError when the node input/ directory is missing.
"""

from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_input_dir_exists(path: PathType) -> None:
    if not Path.is_dir(path):
        raise FileNotFoundError(f"[_validate_node] Node input/ not found: {path}")
```

### platform/shell/structure/node/node/internal/_assert_node_dir_is_dir.py
```
"""_assert_node_dir_is_dir.py
Responsible for one thing: raising FileNotFoundError when a node directory does not exist.
"""

from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_node_dir_is_dir(path: PathType, context: str) -> None:
    if not Path.is_dir(path):
        raise FileNotFoundError(f"[{context}] Node directory not found: {path}")
```

### platform/shell/structure/node/node/internal/_assert_node_dir_set.py
```
"""_assert_node_dir_set.py
Responsible for one thing: raising ValueError when node_dir is not set.
"""

from __future__ import annotations


def _assert_node_dir_set(node_dir: str | None) -> None:
    if node_dir is None:
        raise ValueError("[Node] node_dir is not set")
```

### platform/shell/structure/node/node/internal/_assert_node_name_resolvable.py
```
"""_assert_node_name_resolvable.py
Responsible for one thing: raising ValueError when neither _node_name nor _node_dir is set.
"""


def _assert_node_name_resolvable(node_name: str | None, node_dir: str | None) -> None:
    """Raise ValueError if both node_name and node_dir are falsy."""
    if not node_name and not node_dir:
        raise ValueError("[Node] _node_name is not set and _node_dir is not set")
```

### platform/shell/structure/node/node/internal/_assert_source_dir_set.py
```
from __future__ import annotations

from shell.utils.path.path import PathType



def _assert_source_dir_set(source_dir: PathType | None) -> None:
    if source_dir is None:
        raise RuntimeError("[Node] source_dir is not set — pass --source-dir to the CLI")
```

### platform/shell/structure/node/node/internal/_clean_dir.py
```
"""_clean_dir.py
Remove all files and subdirectories inside a single directory.
"""
from __future__ import annotations

from collections.abc import Callable

from shell.utils.path.path import Path, PathType


def _clean_dir(
    target: PathType,
    rmtree: Callable[[PathType], None] | None = None,
    unlink: Callable[[PathType], None] | None = None,
) -> None:
    """Remove all contents of *target* directory (if it exists).

    Does NOT remove the directory itself.
    """
    if not Path.exists(target):
        return
    if rmtree is None:
        rmtree = Path.rmtree
    if unlink is None:
        unlink = Path.unlink
    for item in Path.iterdir(target):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                unlink(item)
            elif Path.is_dir(item):
                rmtree(item)
        except OSError:
            pass
```

### platform/shell/structure/node/node/internal/_clean_input.py
```
"""_clean_input.py
Responsible for one thing: removing all contents of the input/ directory inside a node.
"""

from __future__ import annotations

from collections.abc import Callable

from shell.utils.path.path import Path, PathType


def _clean_input(
    node: PathType,
    rmtree: Callable[[PathType], None] | None = None,
    unlink: Callable[[PathType], None] | None = None,
) -> None:
    """Remove all files and subdirectories inside <node>/input/."""
    if rmtree is None:
        rmtree = Path.rmtree
    if unlink is None:
        unlink = Path.unlink
    target = node / ".node" / "input"
    if not Path.exists(target):
        return
    for item in Path.iterdir(target):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                unlink(item)
            elif Path.is_dir(item):
                rmtree(item)
        except OSError:
            pass
```

### platform/shell/structure/node/node/internal/_clean_node.py
```
from __future__ import annotations


def _clean_node(node) -> None:
    node.node_input_.clean_node_input()
    node.node_output_.clean_node_output()
    node.node_temp_.clean_node_temp()
    node.node_scripts_.clean_node_scripts()
    node.node_logs_.clean_node_logs()
    node.node_stage_.clean_node_stage()
    node.node_archive_.clean_node_archive()
```

### platform/shell/structure/node/node/internal/_clean_output.py
```
"""_clean_output.py
Responsible for one thing: removing all contents of the output/ directory inside a node.
"""

from __future__ import annotations

from collections.abc import Callable

from shell.utils.path.path import Path, PathType


def _clean_output(
    node: PathType,
    rmtree: Callable[[PathType], None] | None = None,
    unlink: Callable[[PathType], None] | None = None,
) -> None:
    """Remove all files and subdirectories inside <node>/output/."""
    if rmtree is None:
        rmtree = Path.rmtree
    if unlink is None:
        unlink = Path.unlink
    target = node / ".node" / "output"
    if not Path.exists(target):
        return
    for item in Path.iterdir(target):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                unlink(item)
            elif Path.is_dir(item):
                rmtree(item)
        except OSError:
            pass
```

### platform/shell/structure/node/node/internal/_create_node.py
```
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE

if TYPE_CHECKING:
    from shell.app.app_trace.app_trace import AppTrace

_DOT_NODE_DIRS = ("input", "output", "archive", "temp", "logs", "config", "scripts")


def _create_node(node_dir: PathType, make_dirs: Callable[[PathType], None], trace: 'AppTrace | None' = None) -> None:
    dot_node = node_dir / DOT_NODE
    for sub in _DOT_NODE_DIRS:
        path = dot_node / sub
        make_dirs(path)
        if not Path.exists(path):
            raise RuntimeError(f'[node._create_node] failed to create directory: {path}')
        # if trace is not None:
        #     trace.record_info('node._create_node._create_node', f'mkdir {path}')
```

### platform/shell/structure/node/node/internal/_init_node.py
```
from __future__ import annotations


from shell.structure.node.node.internal._validate_node import _validate_node
from shell.structure.node.node.internal._assert_source_dir_set import _assert_source_dir_set
from shell.utils.path.path import Path, PathType

def _init_node(node, node_dir: str, node_config=None) -> None:
    node._node_dir = node_dir
    node._node_name = Path.new(node_dir).name
    node_dir = node.node_dir_

    node.node_config_.init_node_config()
    node.node_input_.init_node_input()
    node.node_output_.init_node_output()
    node.node_logs_.init_node_logs()
    node.node_archive_.init_node_archive()

    source_dir = node._app.cli_.cli_properties_.source_dir_
    _assert_source_dir_set(source_dir)
    if node._app.cli_.cli_properties_.mode_ == 'agent':
        node.node_prompt_.init_node_prompt()
    if node._app.cli_.cli_properties_.mode_ == 'router':
        node.node_stage_.init_node_stage()
    if node._app.cli_.cli_properties_.mode_ == 'tasker':
        node.node_task_.init_node_task()
    _validate_node(node_dir)
```

### platform/shell/structure/node/node/internal/_validate_node.py
```
from __future__ import annotations

from shell.utils.path.path import PathType


from shell.structure.node.node.internal._assert_node_dir_is_dir import _assert_node_dir_is_dir
from shell.structure.node.node.internal._assert_config_yaml_exists import _assert_config_yaml_exists
from shell.structure.node.node.internal._assert_input_dir_exists import _assert_input_dir_exists
from shell.constants.constants import DOT_NODE, CONFIG_DIR, CONFIG_YAML, DIR_INPUT


def _validate_node(node_dir: PathType) -> None:
    _assert_node_dir_is_dir(node_dir, '_validate_node')
    _assert_config_yaml_exists(node_dir / DOT_NODE / CONFIG_DIR / CONFIG_YAML)
    _assert_input_dir_exists(node_dir / DOT_NODE / DIR_INPUT)
```

### platform/shell/structure/node/node/node.py
```
"""node.py
Node — single entry point for all node directory operations.

Slots (own, private):
    _node_dir    — raw path string to the node directory (str | None)
    _node_config — lazy NodeConfig instance (NodeConfig | None)
    node_output  — lazy NodeOutput instance (NodeOutput | None)
    node_input   — lazy NodeInput instance (NodeInput | None)

Validated properties:
    node_dir_    — resolved Path from _node_dir; required, raises if not set
    node_name_   — directory name of node_dir_ as node identifier
    node_config_ — lazy NodeConfig instance

Methods:
    clean_node(rmtree, unlink)     — remove output/ archive/ contents
    init_node()             — validate + create dirs
"""

from __future__ import annotations

from shell.structure.node.node.internal._init_node import _init_node
from shell.structure.node.node.internal._clean_node import _clean_node
from shell.structure.node.node.internal._assert_node_dir_set import _assert_node_dir_set
from shell.structure.node.node_archive.node_archive import NodeArchive
from shell.structure.node.node_config.node_config import NodeConfig
from shell.structure.node.node_input.node_input import NodeInput
from shell.structure.node.node_output.node_output import NodeOutput
from shell.structure.node.node_prompt.node_prompt import NodePrompt
from shell.structure.node.node_logs.node_logs import NodeLogs
from shell.structure.node.node_scripts.node_scripts import NodeScripts
from shell.structure.node.node_task.node_task import NodeTask
from shell.structure.node.node_status.node_status import NodeStatus
from shell.structure.node.node_stage.node_stage import NodeStage
from shell.structure.node.node_temp.node_temp import NodeTemp
from shell.status.status import Status

class Node:
    """Typed interface for all node directory operations.

    Owns _node_dir and _config_node. All node-related logic passes through here.
    _app is kept for operations that need logging and runner_root_dir fallback.
    """

    __slots__ = ("_node_dir", "_node_name", "_node_config", "_app", "_node_status", "_node_output", "_node_input", "_node_archive", "_node_prompt", "_node_task", "_node_stage", "_node_logs", "_node_temp", "_node_scripts")

    def __init__(self, app, node_name: str | None = None,
                 role: str | None = None, type: str | None = None, status: Status | None = None) -> None:
        self._app = app
        self._node_dir: str | None = None
        self._node_name: str | None = node_name
        self._node_config: NodeConfig | None = None
        self._node_output: NodeOutput | None = None
        self._node_input: NodeInput | None = None
        self._node_archive: NodeArchive | None = None
        self._node_status = NodeStatus(status)
        self._node_prompt: NodePrompt | None = None
        self._node_task: NodeTask | None = None
        self._node_stage: NodeStage | None = None
        self._node_logs: NodeLogs | None = None
        self._node_temp: NodeTemp | None = None
        self._node_scripts: NodeScripts | None = None

    # -----------------------------------------------------------------------
    # Validated properties (suffix _ convention)
    # -----------------------------------------------------------------------

    @property
    def node_dir_(self) -> Path:
        """Return resolved Path of node_dir. Raises if not set."""
        _assert_node_dir_set(self._node_dir)
        return Path(self._node_dir).resolve()

    @property
    def node_name_(self) -> str:
        """Return the node name: explicit _node_name if set, else directory name of node_dir_."""
        return self._node_name if self._node_name else self.node_dir_.name

    @property
    def node_status_(self) -> NodeStatus:
        """Return the NodeStatus instance for this node."""
        return self._node_status

    @property
    def status_(self) -> Status | None:
        return self._node_status.status_

    @property
    def is_ready_(self) -> bool:
        """Return True when node should be executed (status 'ready')."""
        return self._node_status.is_ready_

    @property
    def node_config_(self) -> NodeConfig:
        """Lazy NodeConfig instance for this node."""
        if self._node_config is None:
            self._node_config = NodeConfig(self._app)
        return self._node_config

    @property
    def node_output_(self) -> NodeOutput:
        """Lazy NodeOutput instance for this node."""
        if self._node_output is None:
            self._node_output = NodeOutput(self._app)
        return self._node_output

    @property
    def node_input_(self) -> NodeInput:
        """Lazy NodeInput instance for this node."""
        if self._node_input is None:
            self._node_input = NodeInput(self._app)
        return self._node_input

    @property
    def node_prompt_(self) -> NodePrompt:
        if self._node_prompt is None:
            self._node_prompt = NodePrompt(self._app)
        return self._node_prompt

    @property
    def node_task_(self) -> NodeTask:
        if self._node_task is None:
            self._node_task = NodeTask(self._app)
        return self._node_task

    @property
    def node_stage_(self) -> NodeStage:
        if self._node_stage is None:
            self._node_stage = NodeStage(self._app)
        return self._node_stage

    @property
    def node_logs_(self) -> NodeLogs:
        if self._node_logs is None:
            self._node_logs = NodeLogs(self._app)
        return self._node_logs

    @property
    def node_archive_(self) -> NodeArchive:
        """Lazy NodeArchive instance for this node."""
        if self._node_archive is None:
            self._node_archive = NodeArchive(self._app)
        return self._node_archive

    @property
    def node_temp_(self) -> NodeTemp:
        if self._node_temp is None:
            self._node_temp = NodeTemp(self._app)
        return self._node_temp

    @property
    def node_scripts_(self) -> NodeScripts:
        if self._node_scripts is None:
            self._node_scripts = NodeScripts(self._app)
        return self._node_scripts

    # -----------------------------------------------------------------------
    # Clean operations
    # -----------------------------------------------------------------------

    def clean_node(self) -> None:
        _clean_node(self)
        self._app.app_trace_.record_info('node.Node.clean_node', 'OK')

    # -----------------------------------------------------------------------
    # Lifecycle operations
    # -----------------------------------------------------------------------

    def init_node(self, node_dir: str) -> None:
        try:
            _init_node(self, node_dir)
        except Exception as exc:
            self._app.app_trace_.record_error_and_raise('node.Node.init_node', exc)



```

### platform/shell/structure/node/node_archive/__init__.py
```
# shell/node_archive package
from shell.structure.node.node_archive.node_archive import NodeArchive
__all__ = ['NodeArchive']
```

### platform/shell/structure/node/node_archive/internal/__init__.py
```
```

### platform/shell/structure/node/node_archive/internal/_clean_node_archive.py
```
from __future__ import annotations

from shell.utils.path.path import Path


def _clean_node_archive(node_archive) -> None:
    node_archive_dir = node_archive.node_archive_dir_
    if not Path.exists(node_archive_dir):
        return
    for item in Path.iterdir(node_archive_dir):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                Path.unlink(item)
            elif Path.is_dir(item):
                Path.rmtree(item)
        except OSError:
            pass
```

### platform/shell/structure/node/node_archive/internal/_save_archive_zip.py
```
"""_save_archive_zip.py
Private. Responsible for one thing: writing a timestamped ZIP archive
containing app metadata and snapshots of input/, output/, logs/, tmp/.
"""

from __future__ import annotations

import json
import zipfile
from collections.abc import Callable
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from shell.utils.path.path import Path, PathType

if TYPE_CHECKING:
    from shell.app.app_trace.app_trace import AppTrace

_SNAPSHOT_DIRS = ("input", "output", "logs", "temp")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _save_archive_zip(
    archive_dir: PathType,
    snapshot: dict,
    clock: Callable[[], datetime] | None = None,
    trace: 'AppTrace | None' = None,
) -> None:
    """Write a .zip archive under archive_dir/ capturing this execution snapshot.

    archive_dir: path to the node's archive/ directory.
    snapshot:    dict from result.runner_result (timestamp, status, role, mode, version, start, stop).
    clock:       optional callable () -> datetime for testability.
    """
    if clock is None:
        clock = _utc_now

    ts_dt = clock()
    meta = dict(snapshot)
    meta['timestamp'] = ts_dt.isoformat()

    role = meta['role']
    status = meta.get('status', 'unknown')
    ts = ts_dt.strftime("%Y%m%d_%H%M%S")
    fname = f"{role}_{ts}_{status}.zip"

    node = archive_dir.parent
    zip_path = archive_dir / fname
    if trace is not None:
        trace.record_info('node_archive._save_archive_zip._save_archive_zip', f'archive_dir exists={Path.exists(archive_dir)} path={archive_dir}')
        trace.record_info('node_archive._save_archive_zip._save_archive_zip', f'zip_path={zip_path}')
        trace.record_info('node_archive._save_archive_zip._save_archive_zip', f'meta={meta}')
    Path.mkdir(archive_dir)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("meta.json", json.dumps(meta, ensure_ascii=False, indent=2))
        if trace is not None:
            trace.record_info('node_archive._save_archive_zip._save_archive_zip', 'meta.json written to zip')
        for sub in _SNAPSHOT_DIRS:
            src = node / sub
            if trace is not None:
                trace.record_info('node_archive._save_archive_zip._save_archive_zip', f'scanning dir={src} exists={Path.exists(src)}')
            if not Path.exists(src):
                continue
            for p in Path.rglob(src, "*"):
                if Path.is_file(p):
                    arcname = f"{sub}/{p.relative_to(src)}"
                    zf.write(p, arcname=arcname)
                    if trace is not None:
                        trace.record_info('node_archive._save_archive_zip._save_archive_zip', f'archive add {arcname}')
    if trace is not None:
        trace.record_info('node_archive._save_archive_zip._save_archive_zip', f'zip written size={zip_path.stat().st_size}B')

```

### platform/shell/structure/node/node_archive/node_archive.py
```
"""node_archive.py  (node_archive)
NodeArchive — single entry point for all node archive operations.

Slots:
    _app            — parent App
    _module_status  — ModuleStatus enum; NEW on construction, INIT after init_node_archive()

Methods:
    save_archive(clock)     — write archive ZIP; never raises
"""

from __future__ import annotations

from shell.utils.path.path import PathType

from collections.abc import Callable
from datetime import datetime

from shell.status.module_status.module_status import ModuleStatus
from shell.structure.node.node_archive.internal._save_archive_zip import _save_archive_zip
from shell.structure.node.node_archive.internal._clean_node_archive import _clean_node_archive
from shell.constants.constants import DOT_NODE, DIR_ARCHIVE


class NodeArchive:
    """Typed interface for node archive operations.

    Slots:
        _app            — parent App
        _module_status  — ModuleStatus; NEW until init_node_archive() is called
    """

    __slots__ = ("_app", "_module_status")

    def __init__(self, app) -> None:
        self._app = app
        self._module_status: ModuleStatus = ModuleStatus.NEW

    @property
    def node_archive_dir_(self) -> PathType:
        return (self._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_ARCHIVE).resolve()

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    def init_node_archive(self) -> None:
        self._module_status = ModuleStatus.INIT

    def clean_node_archive(self) -> None:
        _clean_node_archive(self)

    def save_archive(self, clock: Callable[[], datetime] | None = None) -> None:
        """Write archive ZIP.  Never raises — errors are logged and suppressed.

        clock: optional callable () -> datetime (defaults to datetime.now(utc)).
        """
        try:
            node_archive_dir = self.node_archive_dir_
            runner_result = self._app.result_.runner_result_
            self._app.app_trace_.record_info('node_archive.NodeArchive.save_archive', f'archive_dir={node_archive_dir}')
            self._app.app_trace_.record_info('node_archive.NodeArchive.save_archive', f'runner_result={runner_result}')
            _save_archive_zip(node_archive_dir, runner_result, clock=clock, trace=self._app.app_trace_)
            self._app.app_trace_.record_info('node_archive.NodeArchive.save_archive', 'archive zip written')
        except Exception as exc:
            self._app.app_trace_.record_error('node_archive.NodeArchive.save_archive', exc)
```

### platform/shell/structure/node/node_config/__init__.py
```
from shell.structure.node.node_config.node_config import NodeConfig

__all__ = ["NodeConfig"]
```

### platform/shell/structure/node/node_config/internal/__init__.py
```
```

### platform/shell/structure/node/node_config/internal/_init_node_config.py
```
"""_init_node_config.py
Private. Responsible for one thing: reading config.yaml into NodeConfig._config.
"""

from __future__ import annotations

from shell.app.app.app import App


def _init_node_config(app: App) -> None:
    app.node_config_.init_node_config()
```

### platform/shell/structure/node/node_config/node_config.py
```
"""node_config.py
NodeConfig — loader and holder for node_dir/.node/config/config.yaml.

Slots:
    _app           — parent App (DOM back-reference)
    _config        — Config instance (Config | None)
    _module_status — ModuleStatus enum; NEW on construction, INIT after init_node_config()

Responsibilities:
    Reads config.yaml from the node directory into a Config object.
    Can also be initialised from data (role, type) without reading from disk.
"""

from __future__ import annotations

from shell.component.config.config.config import Config
from shell.status.module_status.module_status import ModuleStatus
from shell.constants.constants import DOT_NODE, CONFIG_DIR, CONFIG_YAML

class NodeConfig:
    """Holds Config object for the node directory.

    Cached via app.node_config_. _config is populated
    by init_node_config() or append_node_config().
    """

    __slots__ = ("_app", "_config", "_module_status")

    def __init__(self, app) -> None:
        self._app = app
        self._config: Config | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW

    # -----------------------------------------------------------------------
    # Validated property
    # -----------------------------------------------------------------------

    @property
    def config_(self) -> Config:
        if self._config is None:
            self._config = Config(self._app)
        return self._config

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    @property
    def config_dir_(self) -> PathType:
        return self._app.app_node_.node_.node_dir_ / DOT_NODE / CONFIG_DIR

    # -----------------------------------------------------------------------
    # Init
    # -----------------------------------------------------------------------

    def init_node_config(self) -> None:
        cfg_path = self.config_dir_ / CONFIG_YAML
        self.config_.init_config(cfg_path, source='node')
        self._module_status = ModuleStatus.INIT
```

### platform/shell/structure/node/node_input/__init__.py
```
# shell/node_input package
from shell.structure.node.node_input.node_input import NodeInput
__all__ = ['NodeInput']
```

### platform/shell/structure/node/node_input/internal/__init__.py
```
# input internal package
```

### platform/shell/structure/node/node_input/internal/_assert_input_dir_exists.py
```
"""_assert_input_dir_exists.py
Validate that the input directory exists and is a directory.
"""

from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_input_dir_exists(input_dir: PathType) -> None:
    if not Path.is_dir(input_dir):
        raise ValueError(f"Input directory does not exist or is not a directory: {input_dir}")
```

### platform/shell/structure/node/node_input/internal/_init_node_input.py
```
from __future__ import annotations

from shell.component.message.message_list.message_list import MessageList
from shell.component.message.message_reader.message_reader import MessageReader
from shell.structure.node.node_input.internal._assert_input_dir_exists import _assert_input_dir_exists
from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_INPUT

_MESSAGE_SUFFIXES = {".yaml", ".yml"}


def _init_node_input(node_input) -> None:
    node_input._input_dir = (node_input._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_INPUT).resolve()
    _assert_input_dir_exists(node_input._input_dir)

    messages = []
    for path in sorted(p for p in Path.iterdir(node_input.input_dir_) if Path.is_file(p) and p.suffix.lower() in _MESSAGE_SUFFIXES):
        reader = MessageReader()
        reader._path = path
        messages.append(reader.read_message_file())

    message_list = MessageList()
    message_list._messages = messages
    node_input._input_message = message_list
```

### platform/shell/structure/node/node_input/node_input.py
```
"""node_input.py
NodeInput: single entry point for reading node input files.

Fields (own):
    input_dir     — path to the input directory (Path)
    input_message — MessageList of loaded messages
    _module_status — ModuleStatus enum; NEW on construction, INIT after init_node_input()

Methods:
    init_node_input() — load all *.yaml files from input_dir into input_message
"""

from __future__ import annotations


from shell.component.message.message_list.message_list import MessageList
from shell.status.module_status.module_status import ModuleStatus
from shell.structure.node.node_input.internal._init_node_input import _init_node_input
from shell.utils.path.path import Path, PathType


class NodeInput:
    """Manages reading of input files for a single node run.

    input_dir must be set before calling init_node_input.
    init_node_input loads all *.yaml files from input_dir into input_message.
    """

    __slots__ = ("_app", "_input_dir", "_module_status", "_input_message")

    def __init__(self, app) -> None:
        self._app = app
        self._input_dir: PathType | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW
        self._input_message: MessageList | None = None

    # -----------------------------------------------------------------------
    # Validated properties
    # -----------------------------------------------------------------------

    @property
    def input_message_(self) -> MessageList:
        return self._input_message

    @property
    def input_dir_(self) -> PathType:
        return self._input_dir

    @property
    def input_files_map_(self) -> dict[File, str]:
        """Return mapping of loaded File objects to their file names."""
        return self._input_files_map

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    def init_node_input(self) -> None:
        _init_node_input(self)
        self._module_status = ModuleStatus.INIT

    def clean_node_input(self) -> None:
        target = self._input_dir
        if not Path.exists(target):
            return
        for item in Path.iterdir(target):
            try:
                if Path.is_file(item) or Path.is_symlink(item):
                    Path.unlink(item)
                elif Path.is_dir(item):
                    Path.rmtree(item)
            except OSError:
                pass
```

### platform/shell/structure/node/node_logs/__init__.py
```
# shell/node_logs package
from shell.structure.node.node_logs.node_logs import NodeLogs
__all__ = ['NodeLogs']
```

### platform/shell/structure/node/node_logs/internal/__init__.py
```
# shell/node_logs/internal package
```

### platform/shell/structure/node/node_logs/internal/_clean_node_logs.py
```
from __future__ import annotations

from shell.utils.path.path import Path


def _clean_node_logs(node_logs) -> None:
    logs_dir = node_logs.logs_dir_
    if not Path.exists(logs_dir):
        return
    for item in Path.iterdir(logs_dir):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                Path.unlink(item)
            elif Path.is_dir(item):
                Path.rmtree(item)
        except OSError:
            pass
```

### platform/shell/structure/node/node_logs/internal/_init_node_logs.py
```
from __future__ import annotations
from shell.constants.constants import DOT_NODE, DIR_LOGS


def _init_node_logs(node_logs) -> None:
    node_logs._logs_dir = (node_logs._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_LOGS).resolve()
```

### platform/shell/structure/node/node_logs/node_logs.py
```
"""node_logs.py
NodeLogs: manages the logs directory for a single node run.

Slots:
    _app            — parent App
    _module_status  — ModuleStatus enum; NEW on construction, INIT after init_node_logs()
"""

from __future__ import annotations

from shell.utils.path.path import PathType


from shell.status.module_status.module_status import ModuleStatus
from shell.structure.node.node_logs.internal._clean_node_logs import _clean_node_logs
from shell.structure.node.node_logs.internal._init_node_logs import _init_node_logs


class NodeLogs:
    """Manages the logs directory for a single node run.

    Slots:
        _app            — parent App
        _module_status  — ModuleStatus; NEW until init_node_logs() is called
    """

    __slots__ = ("_app", "_logs_dir", "_module_status")

    def __init__(self, app) -> None:
        self._app = app
        self._logs_dir: PathType | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW

    # -----------------------------------------------------------------------
    # Validated properties
    # -----------------------------------------------------------------------

    @property
    def logs_dir_(self) -> PathType:
        return self._logs_dir

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    def init_node_logs(self) -> None:
        _init_node_logs(self)
        self._module_status = ModuleStatus.INIT

    def clean_node_logs(self) -> None:
        _clean_node_logs(self)
```

### platform/shell/structure/node/node_output/__init__.py
```
# shell/node_output package
from shell.structure.node.node_output.node_output import NodeOutput
__all__ = ['NodeOutput']
```

### platform/shell/structure/node/node_output/internal/__init__.py
```
# output internal package
```

### platform/shell/structure/node/node_output/internal/_assert_output_dir_exists.py
```
"""_assert_output_dir_exists.py
Validate that the output directory exists and is a directory.
"""

from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_output_dir_exists(output_dir: PathType) -> None:
    if not Path.is_dir(output_dir):
        raise ValueError(f"Output directory does not exist or is not a directory: {output_dir}")
```

### platform/shell/structure/node/node_output/internal/_assert_output_files_found.py
```
from __future__ import annotations

from shell.utils.path.path import PathType


def _assert_output_files_found(output_files: list, output_dir: PathType) -> None:
    if not output_files:
        raise FileNotFoundError(f"[NodeOutput] no file found in output_dir: {output_dir}")
```

### platform/shell/structure/node/node_output/internal/_assert_pending_message_found.py
```
from __future__ import annotations


def _assert_pending_message_found(pending_message) -> None:
    if pending_message is None:
        raise ValueError("[NodeOutput] no PENDING message found in input_message_list")
```

### platform/shell/structure/node/node_output/internal/_clean_node_output.py
```
from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _clean_node_output(node_output) -> None:
    output_dir = node_output.output_dir_
    if not Path.exists(output_dir):
        return
    for item in Path.iterdir(output_dir):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                Path.unlink(item)
            elif Path.is_dir(item):
                Path.rmtree(item)
        except OSError:
            pass
```

### platform/shell/structure/node/node_output/internal/_format_node_output.py
```
from __future__ import annotations

from shell.component.message.message.message import Message
from shell.component.message.message_envelope.message_envelope import MessageEnvelope
from shell.component.message.message_meta.message_meta import MessageMeta
from shell.component.message.message_name.message_name import MessageName
from shell.component.message.message_reader.message_reader import MessageReader
from shell.component.message.message_status.message_status import MessageStatus
from shell.component.message.message_validator.message_validator import MessageValidator
from shell.component.message.message_writer.message_writer import MessageWriter
from shell.component.message.source_type.source_type import SourceType
from shell.structure.node.node_output.internal._assert_output_files_found import _assert_output_files_found
from shell.utils.path.path import Path


def _format_node_output(node_output: object) -> None:
    node = node_output._app.app_node_.node_
    output_dir = node_output.output_dir_
    input_message_list = node.node_input_.input_message_

    pending_message = input_message_list.get_message_by_status(MessageStatus.PENDING)
    input_message_meta = pending_message.message_envelope_.message_meta_
    output_message_meta = MessageMeta.reverse_message_meta(input_message_meta)

    output_files = sorted(p for p in Path.iterdir(output_dir) if Path.is_file(p))
    _assert_output_files_found(output_files, output_dir)

    for file_path in output_files:
        body = Path.read_text(file_path)
        if MessageValidator.is_valid_message(body):
            message = MessageReader.read(file_path)
        else:
            envelope = MessageEnvelope.from_meta_and_payload(output_message_meta, body)
            message = Message.from_envelope(envelope, str(file_path), SourceType.FILE)
            MessageWriter.write(file_path, message)

        meta = message.message_envelope_.message_meta_
        if not MessageName.is_valid_name(file_path.name, meta):
            file_path = MessageName.rename_message(file_path, meta)

        node_output._output_message_.append_message(message)
```

### platform/shell/structure/node/node_output/internal/_init_node_output.py
```
from __future__ import annotations
from shell.constants.constants import DOT_NODE, DIR_OUTPUT


def _init_node_output(node_output) -> None:
    node_output._output_dir = (node_output._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_OUTPUT).resolve()
```

### platform/shell/structure/node/node_output/node_output.py
```
"""node_output.py
NodeOutput: single entry point for writing node output files.

Fields (own):
    output_dir       — path to the output directory (path)
    output_files_map — dict[File, str] mapping each File to its file_name
    _module_status   — ModuleStatus enum; NEW on construction, INIT after init_node_output()

Methods:
    init_node_output() — mark module as initialised
    save_output() — save all files from output_files_map to output_dir
"""

from __future__ import annotations

from shell.utils.path.path import PathType


from shell.component.message.message_list.message_list import MessageList
from shell.utils.file.File import File
from shell.status.module_status.module_status import ModuleStatus
from shell.structure.node.node_output.internal._assert_output_dir_exists import _assert_output_dir_exists
from shell.structure.node.node_output.internal._clean_node_output import _clean_node_output
from shell.structure.node.node_output.internal._init_node_output import _init_node_output
from shell.structure.node.node_output.internal._format_node_output import _format_node_output


class NodeOutput:
    """Manages writing of output files for a single node run.

    output_dir must exist before calling save_output.
    save_output writes all File objects from output_files_map to output_dir.
    """

    __slots__ = ("_app", "_output_dir", "_output_files_map", "_module_status", "_output_message")

    def __init__(self, app) -> None:
        self._app = app
        self._output_dir: PathType | None = None
        self._output_files_map: dict[File, str] = {}
        self._module_status: ModuleStatus = ModuleStatus.NEW
        self._output_message: MessageList | None = None

    # -----------------------------------------------------------------------
    # Validated properties
    # -----------------------------------------------------------------------

    @property
    def output_message_(self) -> MessageList:
        return self._output_message

    @property
    def output_dir_(self) -> PathType:
        return self._output_dir

    @property
    def output_files_map_(self) -> dict[File, str]:
        """Return mapping of File objects to their file names."""
        return self._output_files_map

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    def init_node_output(self) -> None:
        _init_node_output(self)
        self._module_status = ModuleStatus.INIT

    def save_output(self) -> None:
        """Save all files from output_files_map to output_dir.

        output_files_map — dict mapping File -> file_name (str).
        Each File is saved under output_dir / file_name.
        """
        output_dir = self.output_dir_
        for file, file_name in self._output_files_map.items():
            file._file_path = output_dir / file_name
            file.save_file()

    def clean_node_output(self) -> None:
        _clean_node_output(self)

    def format_node_output(self) -> None:
        _format_node_output(self)
```

### platform/shell/structure/node/node_port/__init__.py
```
```

### platform/shell/structure/node/node_port/node_port.py
```
"""node_port.py
NodePort — port (Protocol) abstrakcji storage dla operacji na nodzie.

Definiuje kontrakt wymienny między adapterami:
    - FilesystemNodePort  (domyślny, produkcyjny)
    - DbNodePort          (przyszłość: wszystkie operacje node → baza danych)
    - InMemoryNodePort    (testy: brak I/O)

Konwencja:
    PathType przekazywany do każdej metody jest logicznym identyfikatorem
    (np. node_dir / DIR_INPUT / 'task.md'), a nie bezwzględną ścieżką systemu plików.
    Adapter tłumaczy go na właściwe medium (ścieżka, klucz DB, klucz słownika).
"""

from __future__ import annotations

from shell.utils.path.path import Path, PathType
from typing import Protocol, runtime_checkable
from shell.constants.constants import DIR_INPUT


@runtime_checkable
class NodePort(Protocol):
    """Port definiujący wszystkie operacje I/O na strukturze node.

    Każda implementacja musi zapewnić pełną obsługę tych operacji
    dla swojego medium (filesystem, baza danych, pamięć itp.).
    """

    # -----------------------------------------------------------------------
    # Struktura katalogów / kontenerów
    # -----------------------------------------------------------------------

    def makedirs(self, path: PathType) -> None:
        """Utwórz katalog (wraz z rodzicami) lub odpowiednik w medium.

        Filesystem: path.mkdir(parents=True, exist_ok=True)
        DB:         INSERT INTO nodes(id, type) ON CONFLICT DO NOTHING
        """
        ...

    def exists(self, path: PathType) -> bool:
        """Sprawdź czy ścieżka / rekord istnieje."""
        ...

    def rmtree(self, path: PathType) -> None:
        """Usuń katalog rekurencyjnie lub wszystkie rekordy pod tym węzłem.

        Filesystem: shutil.rmtree(path, ignore_errors=True)
        DB:         DELETE FROM node_files WHERE path LIKE 'prefix%'
        """
        ...

    # -----------------------------------------------------------------------
    # Pliki / rekordy
    # -----------------------------------------------------------------------

    def read_text(self, path: PathType) -> str:
        """Odczytaj zawartość pliku lub rekordu jako tekst."""
        ...

    def write_text(self, path: PathType, content: str) -> None:
        """Zapisz tekst do pliku lub rekordu."""
        ...

    def unlink(self, path: PathType) -> None:
        """Usuń pojedynczy plik / rekord.

        Filesystem: path.unlink(missing_ok=True)
        DB:         DELETE FROM node_files WHERE path = ?
        """
        ...

    def list_files(self, path: PathType, suffix: str) -> list[PathType]:
        """Zwróć listę plików / rekordów w danym katalogu o podanym rozszerzeniu.

        Filesystem: sorted(path.glob(f'*{suffix}'))
        DB:         SELECT path FROM node_files WHERE parent = ? AND suffix = ?
        """
        ...

    def move(self, src: PathType, dst: PathType) -> None:
        """Przenieś plik / rekord z src do dst.

        Filesystem: shutil.move(src, dst)
        DB:         UPDATE node_files SET path = ? WHERE path = ?
        """
        ...
```

### platform/shell/structure/node/node_prompt/__init__.py
```
# shell/node_prompt package
from shell.structure.node.node_prompt.node_prompt import NodePrompt
__all__ = ['NodePrompt']
```

### platform/shell/structure/node/node_prompt/internal/__init__.py
```
# shell/node_prompt/internal package
```

### platform/shell/structure/node/node_prompt/internal/_assert_prompt_dir_exists.py
```
"""_assert_prompt_dir_exists.py
Validate that the prompt directory exists and is a directory.
"""

from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_prompt_dir_exists(prompt_dir: PathType) -> None:
    if not Path.is_dir(Path.new(prompt_dir)):
        raise ValueError(f"Prompt directory does not exist or is not a directory: {prompt_dir}")
```

### platform/shell/structure/node/node_prompt/internal/_init_node_prompt.py
```
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
```

### platform/shell/structure/node/node_prompt/node_prompt.py
```
"""node_prompt.py
NodePrompt: loads all *.prompt.md files from task_dir into a list.

Slots:
    _app           — parent App
    _prompt_dir    — resolved path to the prompt directory
    _prompt        — Prompt instance; file_prompts_ holds loaded *.prompt.md files
    _module_status — ModuleStatus enum; NEW on construction, INIT after init_node_prompt()

Methods:
    init_node_prompt() — load all *.prompt.md files from task_dir into file_prompt_list
"""

from __future__ import annotations

from shell.utils.path.path import PathType


from shell.status.module_status.module_status import ModuleStatus
from shell.structure.node.node_prompt.internal._init_node_prompt import _init_node_prompt
from shell.component.prompt.prompt.prompt import Prompt


class NodePrompt:

    __slots__ = ("_app", "_prompt_dir", "_prompt", "_module_status")

    def __init__(self, app) -> None:
        self._app = app
        self._prompt_dir: PathType | None = None
        self._prompt: Prompt | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW

    @property
    def prompt_dir_(self) -> PathType:
        return self._prompt_dir

    @property
    def prompt_(self) -> Prompt:
        if self._prompt is None:
            self._prompt = Prompt(self._app)
        return self._prompt

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    def init_node_prompt(self) -> None:
        _init_node_prompt(self)
        self._module_status = ModuleStatus.INIT
```

### platform/shell/structure/node/node_scripts/__init__.py
```
```

### platform/shell/structure/node/node_scripts/internal/__init__.py
```
```

### platform/shell/structure/node/node_scripts/internal/_clean_node_scripts.py
```
from __future__ import annotations

from shell.utils.path.path import Path


def _clean_node_scripts(node_scripts) -> None:
    scripts_dir = node_scripts.scripts_dir_
    if not Path.exists(scripts_dir):
        return
    for item in Path.iterdir(scripts_dir):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                Path.unlink(item)
            elif Path.is_dir(item):
                Path.rmtree(item)
        except OSError:
            pass
```

### platform/shell/structure/node/node_scripts/internal/_init_scripts_dir.py
```
from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_SCRIPTS


def _init_scripts_dir(node_scripts) -> None:
    node_scripts._scripts_dir = (node_scripts._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_SCRIPTS).resolve()
    Path.mkdir(node_scripts.scripts_dir_)
```

### platform/shell/structure/node/node_scripts/node_scripts.py
```
"""node_scripts.py
NodeScripts — scripts directory for a single node.

Slots:
    _scripts_dir   — path to the scripts directory
    _module_status — ModuleStatus enum; NEW on construction, INIT after init_node_scripts()
"""

from __future__ import annotations

from shell.utils.path.path import PathType


from shell.status.module_status.module_status import ModuleStatus
from shell.structure.node.node_scripts.internal._init_scripts_dir import _init_scripts_dir
from shell.structure.node.node_scripts.internal._clean_node_scripts import _clean_node_scripts


class NodeScripts:
    """Manages the scripts directory for a single node run."""

    __slots__ = ("_app", "_scripts_dir", "_module_status")

    def __init__(self, app) -> None:
        self._app = app
        self._scripts_dir: PathType | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW

    @property
    def scripts_dir_(self) -> PathType:
        return self._scripts_dir

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    def init_node_scripts(self) -> None:
        _init_scripts_dir(self)
        self._module_status = ModuleStatus.INIT

    def clean_node_scripts(self) -> None:
        _clean_node_scripts(self)
```

### platform/shell/structure/node/node_stage/__init__.py
```
```

### platform/shell/structure/node/node_stage/internal/__init__.py
```
```

### platform/shell/structure/node/node_stage/internal/_clean_node_stage.py
```
from __future__ import annotations


def _clean_node_stage(node_stage) -> None:
    node_stage.stage_active_.clean_stage_active()
    node_stage.stage_pending_.clean_stage_pending()
    node_stage.stage_history_.clean_stage_history()
    node_stage.stage_ignored_.clean_stage_ignored()
    node_stage.stage_dead_.clean_stage_dead()
    node_stage.stage_done_.clean_stage_done()
```

### platform/shell/structure/node/node_stage/internal/_get_active_files.py
```
from __future__ import annotations


from shell.module.router.router.parse_message_filename import parse_message_filename
from shell.utils.path.path import Path, PathType
from shell.constants.constants import DIR_STAGE_ACTIVE


def _get_active_files(node_stage) -> list[PathType]:
    active_dir = node_stage._stage_dir / DIR_STAGE_ACTIVE
    if not Path.exists(active_dir):
        return []
    candidates = [f for f in Path.iterdir(active_dir) if Path.is_file(f)]

    def _msg_id_key(f: PathType) -> int:
        parsed = parse_message_filename(f.name)
        if parsed is None:
            return -1
        try:
            return int(parsed.sequence_id)
        except ValueError:
            return -1

    return sorted(candidates, key=_msg_id_key)
```

### platform/shell/structure/node/node_stage/internal/_get_last_message.py
```
from __future__ import annotations


from shell.utils.path.path import Path, PathType
from shell.constants.constants import DIR_STAGE_DONE


def _get_last_message(node_stage) -> PathType | None:
    done_dir = node_stage._stage_dir / DIR_STAGE_DONE
    if not Path.exists(done_dir):
        return None
    candidates = [f for f in Path.iterdir(done_dir) if Path.is_file(f)]
    if not candidates:
        return None
    return max(candidates, key=lambda f: f.stat().st_mtime)
```

### platform/shell/structure/node/node_stage/internal/_get_pending_files.py
```
from __future__ import annotations


from shell.utils.path.path import Path, PathType
from shell.constants.constants import DIR_STAGE_PENDING


def _get_pending_files(node_stage) -> list[PathType]:
    pending_dir = node_stage._stage_dir / DIR_STAGE_PENDING
    if not Path.exists(pending_dir):
        return []
    return [f for f in Path.iterdir(pending_dir) if Path.is_file(f)]
```

### platform/shell/structure/node/node_stage/internal/_init_node_stage.py
```
from __future__ import annotations
from shell.constants.constants import DOT_NODE, DIR_STAGE


def _init_node_stage(node_stage) -> None:
    node_stage._stage_dir = (node_stage._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_STAGE).resolve()
    node_stage.stage_.init_stage()
```

### platform/shell/structure/node/node_stage/internal/_init_stage_dirs.py
```
from __future__ import annotations


from shell.constants.constants import DIR_STAGE_ACTIVE, DIR_STAGE_PENDING, DIR_STAGE_HISTORY, DIR_STAGE_IGNORED, DIR_STAGE_DEAD, DIR_STAGE_DONE
from shell.utils.path.path import Path, PathType


def _init_stage_dirs(node_stage) -> None:
    stage_dir = node_stage._stage_dir
    for sub in (DIR_STAGE_ACTIVE, DIR_STAGE_PENDING, DIR_STAGE_HISTORY, DIR_STAGE_IGNORED, DIR_STAGE_DEAD, DIR_STAGE_DONE):
        Path.mkdir(stage_dir / sub)
```

### platform/shell/structure/node/node_stage/internal/_move_pending_to_history.py
```
from __future__ import annotations

from shell.utils.path.path import Path


def _move_pending_to_history(node_stage, filename: str) -> None:
    source = node_stage.stage_pending_.pending_dir_ / filename
    dest = node_stage.stage_history_.history_dir_ / filename
    Path.move(source, dest)
```

### platform/shell/structure/node/node_stage/internal/_move_to_dead.py
```
from __future__ import annotations

from shell.utils.path.path import Path


def _move_to_dead(node_stage, filename: str) -> None:
    source = node_stage.stage_pending_.pending_dir_ / filename
    dest = node_stage.stage_dead_.dead_dir_ / filename
    Path.move(source, dest)
```

### platform/shell/structure/node/node_stage/internal/_move_to_history.py
```
from __future__ import annotations

from shell.utils.path.path import Path


def _move_to_history(node_stage, filename: str) -> None:
    source = node_stage.stage_pending_.pending_dir_ / filename
    dest = node_stage.stage_history_.history_dir_ / filename
    Path.move(source, dest)
```

### platform/shell/structure/node/node_stage/internal/_move_to_ignored.py
```
from __future__ import annotations

from shell.utils.path.path import Path


def _move_to_ignored(node_stage, filename: str) -> None:
    source = node_stage.stage_pending_.pending_dir_ / filename
    dest = node_stage.stage_ignored_.ignored_dir_ / filename
    Path.move(source, dest)
```

### platform/shell/structure/node/node_stage/internal/_move_to_pending.py
```
from __future__ import annotations

from shell.utils.path.path import Path


def _move_to_pending(node_stage, filename: str) -> None:
    source = node_stage.stage_active_.active_dir_ / filename
    dest = node_stage.stage_pending_.pending_dir_ / filename
    Path.move(source, dest)
```

### platform/shell/structure/node/node_stage/internal/_save_to_active.py
```
from __future__ import annotations


from shell.utils.path.path import Path, PathType
from shell.constants.constants import DIR_STAGE_ACTIVE


def _save_to_active(node_stage, file: PathType, dest_name: str | None = None) -> None:
    name = dest_name if dest_name is not None else file.name
    dest = node_stage._stage_dir / DIR_STAGE_ACTIVE / name
    Path.copy_to(file, dest)
```

### platform/shell/structure/node/node_stage/internal/_save_to_done.py
```
from __future__ import annotations


from shell.utils.path.path import Path, PathType
from shell.constants.constants import DIR_STAGE_DONE


def _save_to_done(node_stage, file: PathType) -> None:
    dest = node_stage._stage_dir / DIR_STAGE_DONE / file.name
    Path.copy_to(file, dest)
```

### platform/shell/structure/node/node_stage/internal/_save_to_history.py
```
from __future__ import annotations


from shell.utils.path.path import Path, PathType
from shell.constants.constants import DIR_STAGE_HISTORY


def _save_to_history(node_stage, file: PathType) -> None:
    dest = node_stage._stage_dir / DIR_STAGE_HISTORY / file.name
    Path.copy_to(file, dest)
```

### platform/shell/structure/node/node_stage/internal/_save_to_pending.py
```
from __future__ import annotations


from shell.utils.path.path import Path, PathType
from shell.constants.constants import DIR_STAGE_PENDING


def _save_to_pending(node_stage, file: PathType) -> None:
    dest = node_stage._stage_dir / DIR_STAGE_PENDING / file.name
    Path.copy_to(file, dest)
```

### platform/shell/structure/node/node_stage/node_stage.py
```
"""node_stage.py
NodeStage — physical stage directory I/O for a single node.

Slots:
    _stage_dir     — resolved path to the stage directory
    _module_status — ModuleStatus enum; NEW on construction, INIT after init_node_stage()
"""

from __future__ import annotations

from shell.utils.path.path import PathType


from shell.status.module_status.module_status import ModuleStatus
from shell.structure.node.node_stage.internal._init_node_stage import _init_node_stage
from shell.structure.node.node_stage.internal._clean_node_stage import _clean_node_stage
from shell.structure.node.node_stage.internal._move_to_pending import _move_to_pending
from shell.structure.node.node_stage.internal._move_pending_to_history import _move_pending_to_history
from shell.structure.node.node_stage.internal._move_to_history import _move_to_history
from shell.structure.node.node_stage.internal._move_to_ignored import _move_to_ignored
from shell.structure.node.node_stage.internal._move_to_dead import _move_to_dead
from shell.structure.stage.stage.stage import Stage
from shell.structure.stage.stage_active.stage_active import StageActive
from shell.structure.stage.stage_pending.stage_pending import StagePending
from shell.structure.stage.stage_history.stage_history import StageHistory
from shell.structure.stage.stage_ignored.stage_ignored import StageIgnored
from shell.structure.stage.stage_dead.stage_dead import StageDead
from shell.structure.stage.stage_done.stage_done import StageDone


class NodeStage:
    """Physical stage directory I/O — active, pending, history, ignored, dead, done subdirs."""

    __slots__ = ("_app", "_stage_dir", "_module_status", "_stage")

    def __init__(self, app) -> None:
        self._app = app
        self._stage_dir: PathType | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW
        self._stage: Stage | None = None

    @property
    def stage_dir_(self) -> PathType:
        return self._stage_dir

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    @property
    def stage_(self) -> Stage:
        if self._stage is None:
            self._stage = Stage(self._stage_dir, self._app)
        return self._stage

    @property
    def stage_active_(self) -> StageActive:
        return self.stage_.stage_active_

    @property
    def stage_pending_(self) -> StagePending:
        return self.stage_.stage_pending_

    @property
    def stage_history_(self) -> StageHistory:
        return self.stage_.stage_history_

    @property
    def stage_ignored_(self) -> StageIgnored:
        return self.stage_.stage_ignored_

    @property
    def stage_dead_(self) -> StageDead:
        return self.stage_.stage_dead_

    @property
    def stage_done_(self) -> StageDone:
        return self.stage_.stage_done_

    def init_node_stage(self) -> None:
        _init_node_stage(self)
        self._module_status = ModuleStatus.INIT

    def clean_node_stage(self) -> None:
        _clean_node_stage(self)

    def save_to_active(self, file: PathType, dest_name: str | None = None) -> None:
        self.stage_active_.save_stage_active(file, dest_name)

    def save_to_pending(self, file: PathType) -> None:
        self.stage_pending_.save_stage_pending(file)

    def save_to_history(self, file: PathType) -> None:
        self.stage_history_.save_stage_history(file)

    def save_to_done(self, file: PathType) -> None:
        self.stage_done_.save_stage_done(file)

    def move_to_pending(self, filename: str) -> None:
        _move_to_pending(self, filename)

    def move_pending_to_history(self, filename: str) -> None:
        _move_pending_to_history(self, filename)

    def move_to_history(self, filename: str) -> None:
        _move_to_history(self, filename)

    def move_to_ignored(self, filename: str) -> None:
        _move_to_ignored(self, filename)

    def move_to_dead(self, filename: str) -> None:
        _move_to_dead(self, filename)

    def get_active_files(self) -> list[PathType]:
        return self.stage_active_.get_stage_active_files()

    def get_pending_files(self) -> list[PathType]:
        return self.stage_pending_.get_stage_pending_files()

    def get_last_message(self) -> PathType | None:
        return self.stage_done_.get_stage_done_last_message()

```

### platform/shell/structure/node/node_status/__init__.py
```
from shell.structure.node.node_status.node_status import NodeStatus
```

### platform/shell/structure/node/node_status/node_status.py
```
"""node_status.py
NodeStatus — owns and manages the status of a single node.

Slots:
    _status — current Status value (Status | None)

Validated properties:
    status_ — returns current status value

Methods:
    set_status(value) — set status from Status or int
"""

from __future__ import annotations

from shell.status.status import Status


class NodeStatus:
    """Owns and manages the status of a single node."""

    __slots__ = ("_app", "_status")

    def __init__(self, status: Status | int | None = None) -> None:
        self._app = None
        self._status: Status | None = None
        if status is not None:
            self.set_status(status)

    @property
    def status_(self) -> Status | None:
        """Return current status value."""
        return self._status

    @property
    def is_ready_(self) -> bool:
        """Return True when status is READY."""
        return self._status == Status.READY

    def set_status(self, value: Status | int) -> None:
        """Set status from Status enum or int exit code."""
        if isinstance(value, Status):
            self._status = value
        else:
            self._status = Status(value)

    def init_status(self, status_str: str | None) -> None:
        if status_str is None:
            self._status = Status.NULL
        else:
            self._status = Status.from_str(status_str)
```

### platform/shell/structure/node/node_task/__init__.py
```
```

### platform/shell/structure/node/node_task/internal/__init__.py
```
```

### platform/shell/structure/node/node_task/internal/_assert_source_dir_set.py
```
from __future__ import annotations

from shell.utils.path.path import PathType



def _assert_source_dir_set(source_dir: PathType | None) -> None:
    if source_dir is None:
        raise RuntimeError("[NodeTask] source_dir is not set — pass --source-dir to the CLI")
```

### platform/shell/structure/node/node_task/internal/_assert_task_dir_set.py
```
from shell.utils.path.path import PathType


def _assert_task_dir_set(task_dir: PathType | None) -> None:
    if task_dir is None:
        raise RuntimeError("[NodeTask] task_dir is not set — pass --task-dir to the CLI")
```

### platform/shell/structure/node/node_task/internal/_assert_task_md_exists.py
```
from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_task_md_exists(path: PathType) -> None:
    if not Path.is_file(path):
        raise FileNotFoundError(f"[NodeTask] task MD not found: {path}")
```

### platform/shell/structure/node/node_task/internal/_assert_task_name_set.py
```
from __future__ import annotations


def _assert_task_name_set(task_name: str | None) -> None:
    if not task_name:
        raise ValueError("[NodeTask] --task-name is required")
```

### platform/shell/structure/node/node_task/internal/_assert_task_yaml_exists.py
```
from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _assert_task_yaml_exists(path: PathType) -> None:
    if not Path.is_file(path):
        raise FileNotFoundError(f"[NodeTask] task YAML not found: {path}")
```

### platform/shell/structure/node/node_task/internal/_assert_task_yaml_in_task_dir.py
```
from __future__ import annotations

from shell.utils.path.path import PathType



def _assert_task_yaml_in_task_dir(yaml_files: list, task_dir: PathType) -> None:
    if not yaml_files:
        raise FileNotFoundError(f"[NodeTask] no .yaml file found in task_dir: {task_dir}")
```

### platform/shell/structure/node/node_task/internal/_init_node_task.py
```
from __future__ import annotations


from shell.structure.node.node_task.internal._assert_source_dir_set import _assert_source_dir_set
from shell.structure.node.node_task.internal._assert_task_name_set import _assert_task_name_set
from shell.structure.node.node_task.internal._assert_task_yaml_exists import _assert_task_yaml_exists
from shell.structure.node.node_task.internal._assert_task_md_exists import _assert_task_md_exists
from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE, DIR_TASK


def _init_node_task(node_task) -> None:
    node_dir = Path.new(node_task._app.cli_.cli_properties_.node_dir_).resolve()
    save_dir = node_dir / DOT_NODE / DIR_TASK

    source_dir = node_task._app.cli_.cli_properties_.source_dir_
    _assert_source_dir_set(source_dir)
    task_name = node_task._app.cli_.cli_properties_.task_name_
    _assert_task_name_set(task_name)
    task_yaml_path = source_dir / f'{task_name}.yaml'
    task_md_path = source_dir / f'{task_name}.md'
    _assert_task_yaml_exists(task_yaml_path)
    _assert_task_md_exists(task_md_path)

    node_task._task_name = task_name
    node_task._task_yaml_file_body = Path.read_text(task_yaml_path)
    node_task._task_md_file_body = Path.read_text(task_md_path)

    dest = Path.new(save_dir)
    Path.mkdir(dest)
    Path.write_text(dest / f'{task_name}.yaml', node_task._task_yaml_file_body)
    Path.write_text(dest / f'{task_name}.md', node_task._task_md_file_body)

```

### platform/shell/structure/node/node_task/node_task.py
```
"""node_task.py
NodeTask: loads task files from task_dir and saves them to the node's task/ folder.

Slots:
    _app                 — parent App
    _task_name           — name of the task derived from the yaml filename (str | None)
    _task_md_file_body   — raw content of <task_name>.md (str | None)
    _task_yaml_file_body — raw content of <task_name>.yaml (str | None)
    _module_status       — ModuleStatus enum; NEW on construction, INIT after init_node_task()
"""

from __future__ import annotations

from shell.utils.path.path import PathType

import yaml

from shell.status.module_status.module_status import ModuleStatus
from shell.structure.node.node_task.internal._init_node_task import _init_node_task
from shell.module.tasker.internal._assert_task_graph_yaml_valid import _assert_task_graph_yaml_valid


class NodeTask:
    """Loads task files from task_dir and saves them to the node's .node/task/ folder."""

    __slots__ = ("_app", "_task_name", "_task_md_file_body", "_task_yaml_file_body", "_module_status")

    def __init__(self, app) -> None:
        self._app = app
        self._task_name: str | None = None
        self._task_md_file_body: str | None = None
        self._task_yaml_file_body: str | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW

    @property
    def task_name_(self) -> str | None:
        return self._task_name

    @property
    def task_md_file_body_(self) -> str | None:
        return self._task_md_file_body

    @property
    def task_yaml_file_body_(self) -> str | None:
        return self._task_yaml_file_body

    @property
    def task_graph_dict_(self) -> dict:
        graph_yaml = yaml.safe_load(self._task_yaml_file_body)
        _assert_task_graph_yaml_valid(graph_yaml)
        return graph_yaml

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    def init_node_task(self) -> None:
        _init_node_task(self)
        self._module_status = ModuleStatus.INIT
```

### platform/shell/structure/node/node_temp/__init__.py
```
```

### platform/shell/structure/node/node_temp/internal/__init__.py
```
```

### platform/shell/structure/node/node_temp/internal/_clean_node_temp.py
```
from __future__ import annotations

from shell.utils.path.path import Path


def _clean_node_temp(node_temp) -> None:
    temp_dir = node_temp.temp_dir_
    if not Path.exists(temp_dir):
        return
    for item in Path.iterdir(temp_dir):
        try:
            if Path.is_file(item) or Path.is_symlink(item):
                Path.unlink(item)
            elif Path.is_dir(item):
                Path.rmtree(item)
        except OSError:
            pass
```

### platform/shell/structure/node/node_temp/internal/_init_temp_dir.py
```
from __future__ import annotations

from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_TEMP


def _init_temp_dir(node_temp) -> None:
    node_temp._temp_dir = (node_temp._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TEMP).resolve()
    Path.mkdir(node_temp.temp_dir_)
```

### platform/shell/structure/node/node_temp/node_temp.py
```
"""node_temp.py
NodeTemp — temp directory for a single node.

Slots:
    _temp_dir      — path to the temp directory
    _module_status — ModuleStatus enum; NEW on construction, INIT after init_node_temp()
"""

from __future__ import annotations

from shell.utils.path.path import PathType


from shell.status.module_status.module_status import ModuleStatus
from shell.structure.node.node_temp.internal._init_temp_dir import _init_temp_dir
from shell.structure.node.node_temp.internal._clean_node_temp import _clean_node_temp


class NodeTemp:
    """Manages the temp directory for a single node run."""

    __slots__ = ("_app", "_temp_dir", "_module_status")

    def __init__(self, app) -> None:
        self._app = app
        self._temp_dir: PathType | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW

    @property
    def temp_dir_(self) -> PathType:
        return self._temp_dir

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    def init_node_temp(self) -> None:
        _init_temp_dir(self)
        self._module_status = ModuleStatus.INIT

    def clean_node_temp(self) -> None:
        _clean_node_temp(self)
```

### platform/shell/structure/stage/__init__.py
```
from shell.structure.stage.stage.stage import Stage
```

### platform/shell/structure/stage/stage/__init__.py
```
```

### platform/shell/structure/stage/stage/internal/__init__.py
```
```

### platform/shell/structure/stage/stage/internal/_init_stage.py
```
from __future__ import annotations


def _init_stage(stage) -> None:
    stage.stage_active_.init_stage_active()
    stage.stage_pending_.init_stage_pending()
    stage.stage_history_.init_stage_history()
    stage.stage_ignored_.init_stage_ignored()
    stage.stage_dead_.init_stage_dead()
    stage.stage_done_.init_stage_done()
```
