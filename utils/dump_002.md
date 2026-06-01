### platform/shell/component/message/message_validator/internal/_is_valid_message.py
```
from __future__ import annotations

from shell.component.message.message_validator.internal._assert_message_body_valid import _assert_message_body_valid


def _is_valid_message(body: str) -> bool:
    try:
        _assert_message_body_valid(body)
        return True
    except (ValueError, Exception):
        return False
```

### platform/shell/component/message/message_validator/internal/_validate_message_body.py
```
from __future__ import annotations

from shell.component.message.message_validator.internal._assert_message_body_valid import _assert_message_body_valid


def _validate_message_body(body: str) -> None:
    _assert_message_body_valid(body)
```

### platform/shell/component/message/message_validator/message_validator.py
```
from __future__ import annotations

from shell.component.message.message_validator.internal._is_valid_message import _is_valid_message
from shell.component.message.message_validator.internal._validate_message_body import _validate_message_body


class MessageValidator:

    @staticmethod
    def validate_message_body(body: str) -> None:
        _validate_message_body(body)

    @staticmethod
    def is_valid_message(body: str) -> bool:
        return _is_valid_message(body)
```

### platform/shell/component/message/message_writer/__init__.py
```
from shell.component.message.message_writer.message_writer import MessageWriter
```

### platform/shell/component/message/message_writer/internal/_write_message_file.py
```
from __future__ import annotations

import yaml


def _write_message_file(writer: object) -> None:
    data = writer.message_.message_envelope_.to_dict()
    writer.path_.write_text(yaml.dump(data, allow_unicode=True, default_flow_style=False), encoding="utf-8")
```

### platform/shell/component/message/message_writer/message_writer.py
```
from __future__ import annotations

from shell.component.message.message.message import Message
from shell.component.message.message_writer.internal._write_message_file import _write_message_file
from shell.utils.path.path import Path, PathType


class MessageWriter:
    """
    Slots:
        _path    — path to the output file
        _message — message to write
    """

    __slots__ = ("_path", "_message")

    def __init__(self) -> None:
        self._path: PathType | None = None
        self._message: Message | None = None

    @property
    def path_(self) -> PathType:
        return self._path

    @property
    def message_(self) -> Message:
        return self._message

    def write_message_file(self) -> None:
        _write_message_file(self)

    @staticmethod
    def write(path: PathType, message: Message) -> None:
        writer = MessageWriter()
        writer._path = path
        writer._message = message
        writer.write_message_file()
```

### platform/shell/component/message/source_type/__init__.py
```
from shell.component.message.source_type.source_type import SourceType
```

### platform/shell/component/message/source_type/source_type.py
```
from __future__ import annotations

from enum import Enum


class SourceType(str, Enum):
    FILE = "file"
```

### platform/shell/component/placeholders/__init__.py
```
from shell.component.placeholders.placeholders import Placeholders
```

### platform/shell/component/placeholders/internal/__init__.py
```
```

### platform/shell/component/placeholders/internal/_add_placeholder.py
```
from shell.constants.constants import DIR_OUTPUT, DIR_INPUT, DIR_ARCHIVE, DIR_TEMP

_NODE_SUBDIRS = (DIR_OUTPUT, DIR_INPUT, DIR_ARCHIVE, DIR_TEMP)


def _add_placeholder(placeholders, name: str, value: str) -> None:
    token = f'$${name}$$'
    if '_dir' in name or '_path' in name:
        value = value.replace('\\', '/')
    placeholders._placeholder_list.append((token, value))
    if name == 'node_dir':
        for subdir in _NODE_SUBDIRS:
            subdir_name = f'{subdir}_node_dir'
            subdir_value = f'{value}/.node/{subdir}'
            placeholders._placeholder_list.append((f'$${subdir_name}$$', subdir_value))
```

### platform/shell/component/placeholders/internal/_apply.py
```
def _apply(placeholders, text: str) -> str:
    result = text
    for placeholder, value in placeholders._placeholder_list:
        result = result.replace(placeholder, value)
    return result
```

### platform/shell/component/placeholders/internal/_assert_no_unresolved_placeholders.py
```
import re


def _assert_no_unresolved_placeholders(text: str) -> None:
    unresolved = re.findall(r'\$\$[^$]+\$\$', text)
    if unresolved:
        raise ValueError(f"Unresolved placeholders in prompt text: {unresolved}")
```

### platform/shell/component/placeholders/internal/_bind_dict.py
```
from shell.component.placeholders.internal._add_placeholder import _add_placeholder
from shell.component.placeholders.internal._set_placeholder import _set_placeholder


def _bind_dict(placeholders, config_dict: dict) -> None:
    existing_tokens = {token for token, _ in placeholders._placeholder_list}
    for key, value in config_dict.items():
        if isinstance(value, str):
            token = f'$${key}$$'
            if token in existing_tokens:
                _set_placeholder(placeholders, key, value)
            else:
                _add_placeholder(placeholders, key, value)
```

### platform/shell/component/placeholders/internal/_bind_slots.py
```
def _bind_slots(placeholders, obj) -> None:
    for slot in getattr(obj, '__slots__', []):
        value = getattr(obj, slot, None)
        if isinstance(value, str):
            name = slot.lstrip('_')
            placeholders.add_placeholder(name, value)
```

### platform/shell/component/placeholders/internal/_set_placeholder.py
```
def _set_placeholder(placeholders, name: str, value: str) -> None:
    token = f'$${name}$$'
    for index, (placeholder, _) in enumerate(placeholders._placeholder_list):
        if placeholder == token:
            placeholders._placeholder_list[index] = (token, value)
            return
```

### platform/shell/component/placeholders/internal/_wrap.py
```
def _wrap(placeholders, text: str) -> str:
    result = text
    for placeholder, value in placeholders._placeholder_list:
        result = result.replace(value, placeholder)
    return result
```

### platform/shell/component/placeholders/placeholders.py
```
"""placeholders.py
Placeholders — utility class for replacing $$name$$ tokens in prompt text.

Slots:
    _app              — parent App
    _placeholder_list — list of (placeholder, value) tuples
"""

from __future__ import annotations

from shell.component.placeholders.internal._add_placeholder import _add_placeholder
from shell.component.placeholders.internal._apply import _apply
from shell.component.placeholders.internal._assert_no_unresolved_placeholders import _assert_no_unresolved_placeholders
from shell.component.placeholders.internal._bind_dict import _bind_dict
from shell.component.placeholders.internal._bind_slots import _bind_slots
from shell.component.placeholders.internal._set_placeholder import _set_placeholder
from shell.component.placeholders.internal._wrap import _wrap


class Placeholders:
    """Holds a list of placeholder→value pairs and applies them to prompt text."""

    __slots__ = ("_app", "_placeholder_list")

    def __init__(self, app) -> None:
        self._app = app
        self._placeholder_list: list[tuple[str, str]] = []

    @property
    def placeholder_list_(self) -> list[tuple[str, str]]:
        return self._placeholder_list

    def add_placeholder(self, name: str, value: str) -> None:
        _add_placeholder(self, name, value)

    def bind_slots(self, obj) -> None:
        _bind_slots(self, obj)

    def bind_dict(self, config_dict: dict) -> None:
        _bind_dict(self, config_dict)

    def set_placeholder(self, name: str, value: str) -> None:
        _set_placeholder(self, name, value)

    def apply(self, text: str) -> str:
        return _apply(self, text)

    def assert_no_unresolved(self, text: str) -> None:
        _assert_no_unresolved_placeholders(text)

    def wrap(self, text: str) -> str:
        return _wrap(self, text)
```

### platform/shell/component/process/__init__.py
```
from shell.component.process.process.process import Process
```

### platform/shell/component/process/process/internal/_init_process.py
```
from __future__ import annotations

```

### platform/shell/component/process/process/internal/_init_process_agent.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.component.process.process.process import Process


def _init_process_agent(process: 'Process', prompt: str, timeout: int, which=None, os_name=None) -> None:
    process.process_command_.init_process_command_agent(process.app_, prompt, timeout, which, os_name)
```

### platform/shell/component/process/process/internal/_init_process_command.py
```
from __future__ import annotations

```

### platform/shell/component/process/process/internal/_init_process_sub_node.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.component.process.process.process import Process


def _init_process_sub_node(process: 'Process', sub_node, task_dir, python_exe=None) -> None:
    process.process_command_.init_process_command_sub_node(sub_node, task_dir, process.app_, python_exe)
```

### platform/shell/component/process/process/internal/_init_process_tool.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.component.process.process.process import Process


def _init_process_tool(process: 'Process') -> None:
    app = process.app_
    app_properties = app.app_properties_
    cwd = str(app.app_node_.node_.node_dir_)
    cmd = [app_properties.command_]
    process.process_command_.init_process_command(cmd=cmd, cwd=cwd, timeout=app_properties.timeout_)
```

### platform/shell/component/process/process/internal/_init_process_worker.py
```
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.component.process.process.process import Process


def _init_process_worker(process: 'Process') -> None:
    app = process.app_
    app_properties = app.app_properties_
    cwd = str(app.app_node_.node_.node_dir_)
    if app_properties.type_ == 'python_module':
        cmd = [sys.executable, '-m', app_properties.command_]
    else:
        cmd = [app_properties.command_]
    process.process_command_.init_process_command(cmd=cmd, cwd=cwd, timeout=app_properties.timeout_)
```

### platform/shell/component/process/process/internal/_run_process.py
```
from __future__ import annotations


def _run_process(process: 'Process') -> None:
    pc = process.process_command_
    kwargs = {
        'capture_output': True,
        'text': True,
        'encoding': 'utf-8',
        'errors': 'replace',
        'cwd': pc.cwd_,
    }
    if pc.stdin_ is not None:
        kwargs['input'] = pc.stdin_
    if pc.timeout_ is not None:
        kwargs['timeout'] = pc.timeout_
    if pc.env_ is not None:
        kwargs['env'] = pc.env_
    completed = process._runner(pc.cmd_, **kwargs)
    process._returncode = completed.returncode
    process._stdout = completed.stdout
    process._stderr = completed.stderr
```

### platform/shell/component/process/process/process.py
```
"""process.py
Process: wrapper for a single subprocess invocation.

Slots:
    _app             — parent app
    _process_command — ProcessCommand; all subprocess parameters
    _runner          — Callable; subprocess runner (default: subprocess.run)
    _returncode      — int; exit code of the process
    _stdout          — str; captured stdout
    _stderr          — str; captured stderr
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable

from shell.component.process.process_command.process_command import ProcessCommand
from shell.component.process.process.internal._run_process import _run_process
from shell.component.process.process.internal._init_process_agent import _init_process_agent
from shell.component.process.process.internal._init_process_worker import _init_process_worker
from shell.component.process.process.internal._init_process_tool import _init_process_tool
from shell.component.process.process.internal._init_process_sub_node import _init_process_sub_node


class Process:
    """Represents a single subprocess invocation and its result."""

    __slots__ = ("_app", "_process_command", "_runner", "_returncode", "_stdout", "_stderr")

    def __init__(self, app, runner: Callable[..., subprocess.CompletedProcess] | None = None) -> None:
        self._app = app
        self._process_command: ProcessCommand | None = None
        self._runner: Callable[..., subprocess.CompletedProcess] = runner if runner is not None else subprocess.run
        self._returncode: int | None = None
        self._stdout: str | None = None
        self._stderr: str | None = None

    @property
    def app_(self):
        return self._app

    @property
    def process_command_(self) -> ProcessCommand:
        if self._process_command is None:
            self._process_command = ProcessCommand()
        return self._process_command

    @property
    def returncode_(self) -> int | None:
        return self._returncode

    @property
    def stdout_(self) -> str | None:
        return self._stdout

    @property
    def stderr_(self) -> str | None:
        return self._stderr

    def init_process_agent(self, prompt: str, timeout: int, which=None, os_name=None) -> None:
        _init_process_agent(self, prompt, timeout, which, os_name)

    def init_process_worker(self) -> None:
        _init_process_worker(self)

    def init_process_tool(self) -> None:
        _init_process_tool(self)

    def init_process_sub_node(self, sub_node, task_dir, python_exe=None) -> None:
        _init_process_sub_node(self, sub_node, task_dir, python_exe)

    def run_process(self) -> None:
        _run_process(self)
```

### platform/shell/component/process/process_command/internal/_assert_add_dir_exists.py
```
from shell.utils.path.path import Path, PathType


def _assert_add_dir_exists(add_dir: PathType) -> None:
    if not Path.is_dir(add_dir):
        raise FileNotFoundError(f"Add directory does not exist: {add_dir}")
```

### platform/shell/component/process/process_command/internal/_assert_copilot_cmd_found.py
```
def _assert_copilot_cmd_found(command) -> None:
    if not command:
        raise FileNotFoundError(
            "Agent CLI not found. Set command in app/app.yaml "
            "or ensure the binary is on PATH."
        )
```

### platform/shell/component/process/process_command/internal/_assert_log_dir_exists.py
```
from shell.utils.path.path import Path, PathType


def _assert_log_dir_exists(log_dir: PathType) -> None:
    if not Path.is_dir(log_dir):
        raise FileNotFoundError(f"Log directory does not exist: {log_dir}")
```

### platform/shell/component/process/process_command/internal/_assert_model_set.py
```
def _assert_model_set(model: str) -> None:
    if not model:
        raise ValueError("[ProcessCommand] Required field missing: 'model'")
```

### platform/shell/component/process/process_command/internal/_assert_output_dir_exists.py
```
from shell.utils.path.path import Path, PathType


def _assert_output_dir_exists(output_dir: PathType) -> None:
    if not Path.is_dir(output_dir):
        raise FileNotFoundError(f"Output directory does not exist: {output_dir}")
```

### platform/shell/component/process/process_command/internal/_assert_source_dir_set.py
```
def _assert_source_dir_set(source_dir) -> None:
    if not source_dir:
        raise RuntimeError("[ProcessCommand] source_dir is not set — pass --source-dir to the CLI")
```

### platform/shell/component/process/process_command/internal/_assert_task_dir_set.py
```
def _assert_task_dir_set(task_dir) -> None:
    if not task_dir:
        raise RuntimeError("[ProcessCommand] task_dir is not set — pass --task-dir to the CLI")
```

### platform/shell/component/process/process_command/internal/_assert_task_name_set.py
```
def _assert_task_name_set(task_name) -> None:
    if not task_name:
        raise RuntimeError("[ProcessCommand] task_name is not set — pass --task-name to the CLI")
```

### platform/shell/component/process/process_command/internal/_assert_work_dir_set.py
```
def _assert_work_dir_set(work_dir) -> None:
    if not work_dir:
        raise RuntimeError("[ProcessCommand] work_dir is not set — pass --work-dir to the CLI")
```

### platform/shell/component/process/process_command/internal/_init_process_command.py
```
from __future__ import annotations


def _init_process_command(process_command: 'ProcessCommand', cmd: list[str], cwd: str, stdin: str | None = None, timeout: int | None = None, env: dict | None = None) -> None:
    process_command._cmd = cmd
    process_command._stdin = stdin
    process_command._timeout = timeout
    process_command._cwd = cwd
    process_command._env = env
    if process_command._cmd is None:
        raise ValueError("ProcessCommand._cmd is required")
    if process_command._cwd is None:
        raise ValueError("ProcessCommand._cwd is required")
```

### platform/shell/component/process/process_command/internal/_init_process_command_agent.py
```
from __future__ import annotations

import os
import shutil

from shell.component.command.command import Command
from shell.component.process.process_command.internal._init_process_command import _init_process_command
from shell.component.process.process_command.internal._assert_copilot_cmd_found import _assert_copilot_cmd_found
from shell.component.process.process_command.internal._assert_model_set import _assert_model_set
from shell.component.process.process_command.internal._assert_output_dir_exists import _assert_output_dir_exists
from shell.component.process.process_command.internal._assert_log_dir_exists import _assert_log_dir_exists
from shell.component.process.process_command.internal._assert_add_dir_exists import _assert_add_dir_exists
from shell.constants.constants import DOT_NODE, DIR_OUTPUT


def _init_process_command_agent(process_command, app, prompt, timeout, which=None, os_name=None) -> None:
    which = which or shutil.which
    os_name = os_name or os.name

    command = Command([])

    binary = which("copilot")
    _assert_copilot_cmd_found(binary)

    if os_name == "nt" and str(binary).lower().endswith((".cmd", ".bat")):
        command.extend_command_args(["cmd", "/c", binary])
    else:
        command.add_command_arg(binary)

    model = (app.runner_.agent_.agent_properties_.model_ or "").strip()
    _assert_model_set(model)
    command.extend_command_args(["--model", model])

    if app.cli_.cli_properties_.is_allow_all_paths_:
        command.add_command_arg("--allow-all-paths")

    if app.cli_.cli_properties_.is_allow_all_tools_:
        command.add_command_arg("--allow-all-tools")

    command.extend_command_args(["--output-format", app.cli_.cli_properties_.output_format_])

    if app.cli_.cli_properties_.is_no_ask_user_:
        command.add_command_arg("--no-ask-user")

    if app.cli_.cli_properties_.is_autopilot_:
        command.add_command_arg("--autopilot")

    output_dir = app.app_node_.node_.node_dir_ / DOT_NODE / DIR_OUTPUT
    _assert_output_dir_exists(output_dir)
    command.extend_command_args(["--add-dir", str(output_dir)])
    app.app_trace_.record_info('process_command._init_process_command_agent', f'--add-dir {output_dir}')

    logs_dir = app.app_node_.node_.node_logs_.logs_dir_
    _assert_log_dir_exists(logs_dir)

    for add_dir in app.cli_.cli_properties_.add_dirs_:
        _assert_add_dir_exists(add_dir)
        command.extend_command_args(["--add-dir", str(add_dir)])
        app.app_trace_.record_info('process_command._init_process_command_agent', f'--add-dir {add_dir}')

    node_dir = app.app_node_.node_.node_dir_
    _assert_add_dir_exists(node_dir)
    command.extend_command_args(["--add-dir", str(node_dir)])
    app.app_trace_.record_info('process_command._init_process_command_agent', f'--add-dir {node_dir}')

    command.extend_command_args(["--log-dir", str(logs_dir)])
    app.app_trace_.record_info('process_command._init_process_command_agent', f'--log-dir {logs_dir}')

    cwd = str(app.app_node_.node_.node_dir_)
    _init_process_command(process_command, cmd=command.command_, cwd=cwd, stdin=prompt, timeout=timeout)
```

### platform/shell/component/process/process_command/internal/_init_process_command_sub_node.py
```
from __future__ import annotations

import os
import sys

from shell.component.command.command import Command
from shell.component.process.process_command.internal._init_process_command import _init_process_command
from shell.component.process.process_command.internal._assert_source_dir_set import _assert_source_dir_set
from shell.component.process.process_command.internal._assert_task_dir_set import _assert_task_dir_set
from shell.component.process.process_command.internal._assert_task_name_set import _assert_task_name_set
from shell.component.process.process_command.internal._assert_work_dir_set import _assert_work_dir_set
from shell.component.process.process_command.internal._assert_model_set import _assert_model_set
from shell.structure.sub_node.sub_node.internal._assert_entrypoint_exists import _assert_entrypoint_exists
from shell.utils.path.path import Path


def _init_process_command_sub_node(process_command, sub_node, task_dir, app, python_exe=None) -> None:
    if python_exe is None:
        python_exe = sys.executable

    sub_node_properties = sub_node.sub_node_properties_
    sub_node_name = sub_node_properties.sub_node_name_
    parent_node_dir = sub_node_properties.parent_node_dir_
    runner_root_dir = sub_node_properties.sub_node_runner_root_dir_
    mode = sub_node_properties.mode_
    model = sub_node_properties.model_
    cli = app.cli_
    task_name = sub_node_properties.task_name_ or cli.task_name_
    source_dir = sub_node_properties.source_dir_ or cli.source_dir_
    work_dir = sub_node_properties.work_dir_ or cli.work_dir_
    thread_id = cli.thread_id_

    _assert_source_dir_set(source_dir)
    _assert_work_dir_set(work_dir)
    _assert_task_name_set(task_name)
    _assert_task_dir_set(task_dir)

    node_dir = Path.new(parent_node_dir) / sub_node_name
    entrypoint_path = Path.new(runner_root_dir).resolve() / 'entrypoint.py'
    _assert_entrypoint_exists(entrypoint_path)

    command = Command([])
    command.extend_command_args([python_exe, str(entrypoint_path)])
    command.extend_command_args(['--node-dir', str(node_dir)])
    command.extend_command_args(['--source-dir', str(source_dir)])
    command.extend_command_args(['--work-dir', str(work_dir)])
    command.extend_command_args(['--task-name', task_name])
    command.extend_command_args(['--task-dir', str(task_dir)])

    if parent_node_dir is not None:
        command.extend_command_args(['--parent-node-dir', str(parent_node_dir)])
        app.app_trace_.record_info('process_command._init_process_command_sub_node', f'parent_node_dir set: {parent_node_dir}')
    else:
        app.app_trace_.record_info('process_command._init_process_command_sub_node', 'parent_node_dir not set')

    if thread_id is not None:
        command.extend_command_args(['--parent-thread-id', thread_id])

    if mode == 'agent':
        _assert_model_set(model)
        command.extend_command_args(['--model', model])

    role = sub_node_properties.role_
    if role is not None:
        command.extend_command_args(['--role', role])

    cwd = str(sub_node.entrypoint_path_.parent)
    env = {**os.environ, 'PYTHONUTF8': '1'}
    _init_process_command(process_command, cmd=command.command_, cwd=cwd, env=env)
```

### platform/shell/component/process/process_command/process_command.py
```
"""process_command.py
ProcessCommand: holds all parameters for a single subprocess invocation.

Slots:
    _cmd     — list[str]; the CLI command arguments
    _stdin   — str | None; text piped to process stdin (optional)
    _timeout — int | None; seconds before TimeoutExpired (optional)
    _cwd     — str; working directory for the process
    _env     — dict | None; environment variables override (optional)
"""

from __future__ import annotations

from shell.component.process.process_command.internal._init_process_command import _init_process_command
from shell.component.process.process_command.internal._init_process_command_agent import _init_process_command_agent
from shell.component.process.process_command.internal._init_process_command_sub_node import _init_process_command_sub_node


class ProcessCommand:
    """Holds all subprocess parameters for a single Process invocation."""

    __slots__ = ("_cmd", "_stdin", "_timeout", "_cwd", "_env")

    def __init__(self) -> None:
        self._cmd: list[str] | None = None
        self._stdin: str | None = None
        self._timeout: int | None = None
        self._cwd: str | None = None
        self._env: dict | None = None

    @property
    def cmd_(self) -> list[str]:
        return self._cmd

    @property
    def stdin_(self) -> str | None:
        return self._stdin

    @property
    def timeout_(self) -> int | None:
        return self._timeout

    @property
    def cwd_(self) -> str:
        return self._cwd

    @property
    def env_(self) -> dict | None:
        return self._env

    def init_process_command(self, cmd: list[str], cwd: str, stdin: str | None = None, timeout: int | None = None, env: dict | None = None) -> None:
        _init_process_command(self, cmd, cwd, stdin, timeout, env)

    def init_process_command_agent(self, app, prompt: str, timeout: int, which=None, os_name=None) -> None:
        _init_process_command_agent(self, app, prompt, timeout, which, os_name)

    def init_process_command_sub_node(self, sub_node, task_dir, app, python_exe=None) -> None:
        _init_process_command_sub_node(self, sub_node, task_dir, app, python_exe)
```

### platform/shell/component/prompt/__init__.py
```
```

### platform/shell/component/prompt/prompt/__init__.py
```
from shell.component.prompt.prompt.prompt import Prompt
```

### platform/shell/component/prompt/prompt/internal/_init_prompt.py
```
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
```

### platform/shell/component/prompt/prompt/prompt.py
```

from __future__ import annotations

from shell.utils.path.path import PathType



from shell.component.prompt_file.prompt_file import PromptFile
from shell.component.prompt.prompt.internal._init_prompt import _init_prompt
from shell.component.prompt.prompt_cli.prompt_cli import PromptCli
from shell.component.prompt.prompt_input.prompt_input import PromptInput
from shell.component.prompt.prompt_role.prompt_role import PromptRole
from shell.component.prompt.prompt_skill.prompt_skill import PromptSkill
from shell.component.prompt.prompt_system.prompt_system import PromptSystem
from shell.component.prompt.prompt_task.prompt_task import PromptTask


class Prompt:

    __slots__ = (
        "_app",
        "_file_prompts",
        "_prompt_dir",
        "_prompt_cli",
        "_prompt_input",
        "_prompt_role",
        "_prompt_skill",
        "_prompt_system",
        "_prompt_task",
    )

    def __init__(self, app) -> None:
        self._app = app
        self._file_prompts: list[PromptFile] = []
        self._prompt_dir: PathType | None = None
        self._prompt_cli: PromptCli | None = None
        self._prompt_input: PromptInput | None = None
        self._prompt_role: PromptRole | None = None
        self._prompt_skill: PromptSkill | None = None
        self._prompt_system: PromptSystem | None = None
        self._prompt_task: PromptTask | None = None

    @property
    def file_prompts_(self) -> list[PromptFile]:
        return self._file_prompts

    @property
    def prompt_dir_(self) -> PathType:
        return self._prompt_dir

    @property
    def prompt_cli_(self) -> PromptCli:
        if self._prompt_cli is None:
            self._prompt_cli = PromptCli(self._app)
        return self._prompt_cli

    @property
    def prompt_input_(self) -> PromptInput:
        if self._prompt_input is None:
            self._prompt_input = PromptInput(self._app)
        return self._prompt_input

    @property
    def prompt_role_(self) -> PromptRole:
        if self._prompt_role is None:
            self._prompt_role = PromptRole(self._app)
        return self._prompt_role

    @property
    def prompt_skill_(self) -> PromptSkill:
        if self._prompt_skill is None:
            self._prompt_skill = PromptSkill(self._app)
        return self._prompt_skill

    @property
    def prompt_system_(self) -> PromptSystem:
        if self._prompt_system is None:
            self._prompt_system = PromptSystem(self._app)
        return self._prompt_system

    @property
    def prompt_task_(self) -> PromptTask:
        if self._prompt_task is None:
            self._prompt_task = PromptTask(self._app)
        return self._prompt_task

    def init_prompt(self) -> None:
        _init_prompt(self)
```

### platform/shell/component/prompt/prompt_cli/__init__.py
```
from shell.component.prompt.prompt_cli.prompt_cli import PromptCli
```

### platform/shell/component/prompt/prompt_cli/internal/__init__.py
```
```

### platform/shell/component/prompt/prompt_cli/internal/_init_prompt_cli.py
```
from shell.component.prompt.prompt_type.prompt_type import PromptType


def _init_prompt_cli(prompt_cli) -> None:
    cli_prompt = prompt_cli._app.cli_.cli_properties_.prompt_
    prompt_cli.prompt_file_._file_name = 'cli.prompt.md'
    prompt_cli.prompt_file_._file_body = cli_prompt
    prompt_cli.prompt_file_._prompt_type = PromptType.CLI
```

### platform/shell/component/prompt/prompt_cli/prompt_cli.py
```
"""prompt_cli.py
PromptCli — holds the CLI-sourced prompt for a single agent run.

Slots:
    _prompt_file — PromptFile built from CLI --prompt arg (PromptFile | None)
"""

from __future__ import annotations

from shell.component.prompt_file.prompt_file import PromptFile
from shell.component.prompt.prompt_cli.internal._init_prompt_cli import _init_prompt_cli


class PromptCli:
    """Holds the CLI-sourced prompt for a single agent run."""

    __slots__ = ("_app", "_prompt_file")

    def __init__(self, app=None) -> None:
        self._app = app
        self._prompt_file: PromptFile | None = None

    @property
    def prompt_file_(self) -> PromptFile:
        if self._prompt_file is None:
            self._prompt_file = PromptFile()
        return self._prompt_file

    def init_prompt_cli(self) -> None:
        _init_prompt_cli(self)
```

### platform/shell/component/prompt/prompt_input/__init__.py
```
from shell.component.prompt.prompt_input.prompt_input import PromptInput

__all__ = ['PromptInput']
```

### platform/shell/component/prompt/prompt_input/internal/_init_prompt_input.py
```
from __future__ import annotations


from shell.component.prompt_file.prompt_file import PromptFile
from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE, DIR_PROMPT


def _init_prompt_input(prompt_input) -> None:
    app = prompt_input._app
    task_dir = Path.new(app.cli_.cli_properties_.task_dir_)
    role = app.app_properties_.role_
    task_name = app.cli_.cli_properties_.task_name_
    prompt_dir = app.app_node_.node_.node_dir_ / DOT_NODE / DIR_PROMPT
    prompt_input._file_prompts = []
    marker = f'.{role}.{task_name}.'
    for path in Path.glob(task_dir, '*.input.prompt.md'):
        if marker not in path.name:
            continue
        body = Path.read_text(path)
        if body:
            file_prompt = PromptFile()
            file_prompt.init_prompt_file(path.name, body, prompt_dir)
            prompt_input._file_prompts.append(file_prompt)
```

### platform/shell/component/prompt/prompt_input/internal/_prompt.py
```
def _prompt(prompt_input) -> str:
    sorted_prompts = sorted(prompt_input._file_prompts, key=lambda p: p._file_name)
    return "\n\n".join(p._file_body for p in sorted_prompts if p._file_body)
```

### platform/shell/component/prompt/prompt_input/prompt_input.py
```
from __future__ import annotations

from shell.component.prompt_file.prompt_file import PromptFile
from shell.component.prompt.prompt_input.internal._init_prompt_input import _init_prompt_input
from shell.component.prompt.prompt_input.internal._prompt import _prompt


class PromptInput:

    __slots__ = ("_app", "_file_prompts")

    def __init__(self, app=None) -> None:
        self._app = app
        self._file_prompts: list[PromptFile] = []

    @property
    def file_prompts_(self) -> list[PromptFile]:
        return self._file_prompts

    def init_prompt_input(self) -> None:
        _init_prompt_input(self)

    def prompt(self) -> str:
        return _prompt(self)
```

### platform/shell/component/prompt/prompt_role/__init__.py
```
from shell.component.prompt.prompt_role.prompt_role import PromptRole
```

### platform/shell/component/prompt/prompt_role/internal/__init__.py
```
```

### platform/shell/component/prompt/prompt_role/internal/_init_prompt_role.py
```
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
```

### platform/shell/component/prompt/prompt_role/internal/_prompt.py
```
def _prompt(prompt_role) -> str:
    sorted_prompts = sorted(prompt_role._file_prompts, key=lambda p: p._file_name)
    return "\n\n".join(p._file_body for p in sorted_prompts if p._file_body)
```

### platform/shell/component/prompt/prompt_role/prompt_role.py
```
"""prompt_role.py
PromptRole — holds a list of PromptFile objects loaded from role prompt files.

Slots:
    _file_prompts — list of PromptFile objects loaded from *.<role>.prompt.md files
"""

from __future__ import annotations

from shell.component.prompt_file.prompt_file import PromptFile
from shell.component.prompt.prompt_role.internal._init_prompt_role import _init_prompt_role
from shell.component.prompt.prompt_role.internal._prompt import _prompt


class PromptRole:
    """Holds role prompts loaded from *.<role>.prompt.md files in task-dir."""

    __slots__ = ("_app", "_file_prompts")

    def __init__(self, app=None) -> None:
        self._app = app
        self._file_prompts: list[PromptFile] = []

    @property
    def file_prompts_(self) -> list[PromptFile]:
        return self._file_prompts

    def init_prompt_role(self) -> None:
        _init_prompt_role(self)

    def prompt(self) -> str:
        return _prompt(self)
```

### platform/shell/component/prompt/prompt_skill/__init__.py
```
```

### platform/shell/component/prompt/prompt_skill/internal/__init__.py
```
```

### platform/shell/component/prompt/prompt_skill/internal/_init_prompt_skill.py
```
from __future__ import annotations


from shell.component.prompt_file.prompt_file import PromptFile
from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE, DIR_PROMPT


def _init_prompt_skill(prompt_skill) -> None:
    app = prompt_skill._app
    task_dir = Path.new(app.cli_.cli_properties_.source_dir_ or app.cli_.cli_properties_.task_dir_)
    task_name = app.cli_.cli_properties_.task_name_
    prompt_dir = app.app_node_.node_.node_dir_ / DOT_NODE / DIR_PROMPT
    prompt_skill._file_prompts = []
    marker = f'.{task_name}.'
    for path in Path.glob(task_dir, '*.skill.prompt.md'):
        if marker not in path.name:
            continue
        body = Path.read_text(path)
        if body:
            file_prompt = PromptFile()
            file_prompt.init_prompt_file(path.name, body, prompt_dir)
            prompt_skill._file_prompts.append(file_prompt)
```

### platform/shell/component/prompt/prompt_skill/internal/_prompt.py
```
def _prompt(prompt_skill) -> str:
    sorted_prompts = sorted(prompt_skill._file_prompts, key=lambda p: p._file_name)
    return "\n\n".join(p._file_body for p in sorted_prompts if p._file_body)
```

### platform/shell/component/prompt/prompt_skill/prompt_skill.py
```
"""prompt_skill.py
PromptSkill — holds a list of PromptFile objects loaded from skill prompt files.

Slots:
    _file_prompts — list of PromptFile objects loaded from *.<task-name>.skill.prompt.md files
"""

from __future__ import annotations

from shell.component.prompt_file.prompt_file import PromptFile
from shell.component.prompt.prompt_skill.internal._init_prompt_skill import _init_prompt_skill
from shell.component.prompt.prompt_skill.internal._prompt import _prompt


class PromptSkill:
    """Holds skill prompts loaded from *.<task-name>.skill.prompt.md files in task-dir."""

    __slots__ = ("_app", "_file_prompts")

    def __init__(self, app=None) -> None:
        self._app = app
        self._file_prompts: list[PromptFile] = []

    @property
    def file_prompts_(self) -> list[PromptFile]:
        return self._file_prompts

    def init_prompt_skill(self) -> None:
        _init_prompt_skill(self)

    def prompt(self) -> str:
        return _prompt(self)
```

### platform/shell/component/prompt/prompt_system/__init__.py
```
from shell.component.prompt.prompt_system.prompt_system import PromptSystem
```

### platform/shell/component/prompt/prompt_system/internal/__init__.py
```
```

### platform/shell/component/prompt/prompt_system/internal/_init_prompt_system.py
```
from __future__ import annotations


from shell.component.prompt_file.prompt_file import PromptFile
from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE, DIR_PROMPT


def _init_prompt_system(prompt_system) -> None:
    app = prompt_system._app
    task_dir = Path.new(app.cli_.cli_properties_.source_dir_ or app.cli_.cli_properties_.task_dir_)
    role = app.app_properties_.role_
    task_name = app.cli_.cli_properties_.task_name_
    prompt_dir = app.app_node_.node_.node_dir_ / DOT_NODE / DIR_PROMPT
    prompt_system._file_prompts = []
    marker = f'.{role}.{task_name}.'
    for path in Path.glob(task_dir, '*.system.prompt.md'):
        if marker not in path.name:
            continue
        body = Path.read_text(path)
        if body:
            file_prompt = PromptFile()
            file_prompt.init_prompt_file(path.name, body, prompt_dir)
            prompt_system._file_prompts.append(file_prompt)
```

### platform/shell/component/prompt/prompt_system/internal/_prompt.py
```
def _prompt(prompt_system) -> str:
    sorted_prompts = sorted(prompt_system._file_prompts, key=lambda p: p._file_name)
    return "\n\n".join(p._file_body for p in sorted_prompts if p._file_body)
```

### platform/shell/component/prompt/prompt_system/prompt_system.py
```
"""prompt_system.py
PromptSystem — holds system prompt list loaded from task-dir.

Slots:
    _file_prompts — list of PromptFile objects (PromptFile)

Loads files matching *.system.prompt.md:
    - <nr>.<role>.system.prompt.md — only if role matches current role
    - <nr>.system.prompt.md        — always loaded (no role indicator)
"""

from __future__ import annotations

from shell.component.prompt_file.prompt_file import PromptFile
from shell.component.prompt.prompt_system.internal._init_prompt_system import _init_prompt_system
from shell.component.prompt.prompt_system.internal._prompt import _prompt


class PromptSystem:
    """Holds system prompts loaded from *.system.prompt.md files in task-dir."""

    __slots__ = ("_app", "_file_prompts")

    def __init__(self, app=None) -> None:
        self._app = app
        self._file_prompts: list[FilePrompt] = []

    @property
    def file_prompts_(self) -> list[FilePrompt]:
        return self._file_prompts

    def init_prompt_system(self) -> None:
        _init_prompt_system(self)

    def prompt(self) -> str:
        return _prompt(self)
```

### platform/shell/component/prompt/prompt_task/__init__.py
```
from shell.component.prompt.prompt_task.prompt_task import PromptTask

__all__ = ['PromptTask']
```

### platform/shell/component/prompt/prompt_task/internal/_init_prompt_task.py
```
from __future__ import annotations


from shell.component.prompt_file.prompt_file import PromptFile
from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE, DIR_PROMPT


def _init_prompt_task(prompt_task) -> None:
    app = prompt_task._app
    task_dir = Path.new(app.cli_.cli_properties_.task_dir_)
    role = app.app_properties_.role_
    task_name = app.cli_.cli_properties_.task_name_
    prompt_dir = app.app_node_.node_.node_dir_ / DOT_NODE / DIR_PROMPT
    prompt_task._file_prompts = []
    marker = f'.{role}.{task_name}.'
    for path in Path.glob(task_dir, '*.task.prompt.md'):
        if marker not in path.name:
            continue
        body = Path.read_text(path)
        if body:
            file_prompt = PromptFile()
            file_prompt.init_prompt_file(path.name, body, prompt_dir)
            prompt_task._file_prompts.append(file_prompt)
```

### platform/shell/component/prompt/prompt_task/internal/_prompt.py
```
def _prompt(prompt_task) -> str:
    sorted_prompts = sorted(prompt_task._file_prompts, key=lambda p: p._file_name)
    return "\n\n".join(p._file_body for p in sorted_prompts if p._file_body)
```

### platform/shell/component/prompt/prompt_task/prompt_task.py
```
from __future__ import annotations

from shell.component.prompt_file.prompt_file import PromptFile
from shell.component.prompt.prompt_task.internal._init_prompt_task import _init_prompt_task
from shell.component.prompt.prompt_task.internal._prompt import _prompt


class PromptTask:

    __slots__ = ("_app", "_file_prompts")

    def __init__(self, app=None) -> None:
        self._app = app
        self._file_prompts: list[PromptFile] = []

    @property
    def file_prompts_(self) -> list[PromptFile]:
        return self._file_prompts

    def init_prompt_task(self) -> None:
        _init_prompt_task(self)

    def prompt(self) -> str:
        return _prompt(self)
```

### platform/shell/component/prompt/prompt_type/__init__.py
```
from shell.component.prompt.prompt_type.prompt_type import PromptType
```

### platform/shell/component/prompt/prompt_type/prompt_type.py
```
"""prompt_type.py
PromptType — enum representing the type of a prompt file.
"""

from __future__ import annotations

from enum import Enum


class PromptType(Enum):
    SYSTEM = 'system'
    ROLE = 'role'
    CLI = 'cli'
    NONE = 'none'
```

### platform/shell/component/prompt_file/__init__.py
```
# shell/prompt_file package
from shell.component.prompt_file.prompt_file import PromptFile
from shell.component.prompt.prompt_type.prompt_type import PromptType
__all__ = ['PromptFile', 'PromptType']
```

### platform/shell/component/prompt_file/internal/__init__.py
```
# shell/prompt_file/internal package
```

### platform/shell/component/prompt_file/internal/_init_prompt_file.py
```

from __future__ import annotations

from shell.utils.path.path import PathType



from shell.component.prompt_file.internal._save_prompt_file import _save_prompt_file
from shell.component.prompt.prompt_type.prompt_type import PromptType


def _init_prompt_file(prompt_file, file_name: str, file_body: str, save_dir: PathType) -> None:
    prompt_file._file_name = file_name
    prompt_file._file_body = file_body
    if '.system.' in file_name:
        prompt_file._prompt_type = PromptType.SYSTEM
    elif '.role.' in file_name or file_name.endswith('.prompt.md'):
        prompt_file._prompt_type = PromptType.ROLE
    else:
        prompt_file._prompt_type = PromptType.NONE
    _save_prompt_file(prompt_file, save_dir)
```

### platform/shell/component/prompt_file/internal/_save_prompt_file.py
```
from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _save_prompt_file(prompt_file, save_dir: PathType) -> None:
    dest = Path.new(save_dir)
    Path.mkdir(dest)
    Path.write_text(dest / prompt_file._file_name, prompt_file._file_body)
```

### platform/shell/component/prompt_file/prompt_file.py
```
"""prompt_file.py
PromptFile — represents a single prompt file loaded from disk.

Slots:
    _file_name    — file name (str)
    _file_body    — file content (str)
    _prompt_type  — prompt type derived from file name (str)
"""

from __future__ import annotations

from shell.utils.path.path import PathType



from shell.component.prompt_file.internal._init_prompt_file import _init_prompt_file
from shell.component.prompt_file.internal._save_prompt_file import _save_prompt_file
from shell.component.prompt.prompt_type.prompt_type import PromptType


class PromptFile:
    """Represents a single prompt file.

    Slots:
        _file_name    — file name (str)
        _file_body    — file content (str)
        _prompt_type  — prompt type derived from file name (str)
    """

    __slots__ = ("_file_name", "_file_body", "_prompt_type")

    def __init__(self) -> None:
        self._file_name: str = ""
        self._file_body: str = ""
        self._prompt_type: PromptType = PromptType.NONE

    @property
    def file_name_(self) -> str:
        return self._file_name

    @property
    def file_body_(self) -> str:
        return self._file_body

    @property
    def prompt_type_(self) -> PromptType:
        return self._prompt_type

    def init_prompt_file(self, file_name: str, file_body: str, save_dir: PathType) -> None:
        _init_prompt_file(self, file_name, file_body, save_dir)

    def save_prompt_file(self, save_dir) -> None:
        _save_prompt_file(self, save_dir)
```

### platform/shell/component/result/__init__.py
```
from shell.component.result.result import Result
from shell.status.status import Status

__all__ = ["Result", "Status"]
```

### platform/shell/component/result/internal/__init__.py
```
from shell.component.result.internal._save_result import _save_result

__all__ = ["_save_result"]
```

### platform/shell/component/result/internal/_save_result.py
```
"""_save_result.py
Responsible for one thing: persisting the graph result to .node/result/.

Files written:
    .node/result/stdout.md   — subprocess stdout (only when non-empty)
    .node/result/stderr.md   — subprocess stderr (only when non-empty)
    .node/result/result.yaml — returncode, start_time, stop_time (ISO format)
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from shell.utils.path.path import Path, PathType

if TYPE_CHECKING:
    from shell.app.app_trace.app_trace import AppTrace
    from shell.component.result.result import Result

_RESULT_DIR = Path.new(".node") / "result"
_STDOUT_FILE = _RESULT_DIR / "stdout.md"
_STDERR_FILE = _RESULT_DIR / "stderr.md"
_RESULT_YAML = _RESULT_DIR / "result.yaml"


def _save_result(node: PathType, result: 'Result', start_dt: datetime | None = None, stop_dt: datetime | None = None, trace: 'AppTrace | None' = None) -> None:
    """Write stdout, stderr and result.yaml into <node>/.node/result/.

    stdout.md and stderr.md are only written when content is non-empty.
    result.yaml is always written.
    """
    result_dir = node / _RESULT_DIR
    Path.mkdir(result_dir)
    if trace is not None:
        trace.record_info('result._save_result._save_result', f'mkdir {result_dir}')

    if result._stdout and result._stdout.strip():
        stdout_path = node / _STDOUT_FILE
        Path.write_text(stdout_path, result._stdout)
        if trace is not None:
            trace.record_info('result._save_result._save_result', f'write {stdout_path}')

    if result._stderr and result._stderr.strip():
        stderr_path = node / _STDERR_FILE
        Path.write_text(stderr_path, result._stderr)
        if trace is not None:
            trace.record_info('result._save_result._save_result', f'write {stderr_path}')

    returncode = int(result._status) if result._status is not None else 1
    start_iso = start_dt.isoformat() if start_dt is not None else None
    stop_iso = stop_dt.isoformat() if stop_dt is not None else None

    yaml_content = (
        f"returncode: {returncode}\n"
        f"start_time: {start_iso}\n"
        f"stop_time: {stop_iso}\n"
    )
    result_yaml_path = node / _RESULT_YAML
    Path.write_text(result_yaml_path, yaml_content)
    if trace is not None:
        trace.record_info('result._save_result._save_result', f'write {result_yaml_path}')
```

### platform/shell/component/result/result.py
```
"""result.py
Result — singleton execution result for a single shell graph run.

Klasa `Result` jest tworzona raz na uruchomienie i aktualizowana
w miejscach, gdzie runner kończy pracę lub subproces zwraca wynik.

__slots__:
    _app  — referencja do App (DOM back-reference)
    status          — semantyczny wynik z perspektywy graph
                      ('success', 'error', 'timeout', 'warning', 'locked',
                       'question', 'waiting', 'skip', 'critical')
    stdout          — standardowe wyjście subprocesu
    stderr          — wyjście błędów subprocesu
    returncode      — niskopoziomowy kod wyjścia subprocesu (int | None)
    returncode_     — property: returncode lub CRITICAL(10) gdy slot jest None

Rozróżnienie status vs returncode:
    returncode — techniczny wynik subprocesu (0 = sukces, inne = błąd)
    status     — semantyczny wynik graph (returncode=0 może dać status=waiting)
"""

from __future__ import annotations

from shell.utils.path.path import Path, PathType
from typing import TYPE_CHECKING

from shell.component.result.internal._save_result import _save_result
from shell.status.status import Status

if TYPE_CHECKING:
    from shell.app.app.app import App
    from shell.app.app_trace.app_trace import AppTrace


class Result:
    """Singleton execution result for a single graph run."""

    Status = Status

    _TERMINAL_STATUSES: frozenset = frozenset({Status.ERROR, Status.LOCKED, Status.CRITICAL})

    __slots__ = (
        "_app",
        "_status",
        "_stdout",
        "_stderr",
        "_returncode",
    )

    def __init__(self, app: 'App | None' = None) -> None:
        self._app: App | None = app
        self._status: Status = Status.NULL
        self._stdout: str | None = None
        self._stderr: str | None = None
        self._returncode: int | None = None

    # -----------------------------------------------------------------------
    # Factory
    # -----------------------------------------------------------------------

    @classmethod
    def from_trace(cls, trace: 'AppTrace', app: 'App | None' = None) -> 'Result':
        """Construct a Result from a completed AppTrace.

        Status resolution priority:
          1. any error event  → ERROR,  returncode=1
          2. any warning event → WARNING, returncode=2
          3. otherwise        → SUCCESS, returncode=0
        """
        result = cls(app)
        result._stdout = trace.stdout_
        result._stderr = trace.stderr_
        result._returncode = trace.returncode_
        if trace.has_errors_:
            result._status = Status.ERROR
        elif trace.has_warnings_:
            result._status = Status.WARNING
        else:
            result._status = Status.SUCCESS
        return result

    # -----------------------------------------------------------------------
    # Status predicates
    # -----------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"Result(status={self._status!r}, returncode={self._returncode!r})"

    @property
    def status_(self) -> Status:
        """Return current graph status."""
        return self._status

    def set_status(self, status: Status) -> None:
        self._status = status

    @property
    def stdout_(self) -> str | None:
        """Return subprocess stdout."""
        return self._stdout

    @property
    def stderr_(self) -> str | None:
        """Return subprocess stderr."""
        return self._stderr

    @property
    def returncode_(self) -> int:
        """Return returncode or CRITICAL (10) when slot is None.

        None means the process never started — treated as critical failure.
        """
        if self._returncode is None:
            return Status.CRITICAL
        return self._returncode

    @property
    def is_terminal_(self) -> bool:
        """Return True when status is a terminal (non-retryable) value."""
        return self._status in self._TERMINAL_STATUSES

    @property
    def is_success_(self) -> bool:
        return self._status == Status.SUCCESS

    @property
    def is_error_(self) -> bool:
        return self._status == Status.ERROR

    # -----------------------------------------------------------------------
    # Save result
    # -----------------------------------------------------------------------

    def save_result(self) -> None:
        """Persist stdout, stderr and result.yaml to <node>/.node/result/.

        Node path is resolved from the back-reference to app.
        """
        try:
            node = Path.new(self._app.app_node_.node_.node_dir_)
            start_dt = self._app.app_trace_._start_trace_date_time
            stop_dt = self._app.app_trace_._stop_trace_date_time
            _save_result(node, self, start_dt, stop_dt, self._app.app_trace_)
        except Exception as exc:
            self._app.app_trace_.record_error('result.Result.save_result', exc)

    # -----------------------------------------------------------------------
    # Runner result
    # -----------------------------------------------------------------------

    @property
    def runner_result_(self) -> dict:
        """Return a serialisable execution summary dict.

        Keys: timestamp, status, role, mode, version, start, stop.
        start/stop are ISO-format UTC strings from AppTrace.
        Reads role, mode and version from app when available.
        """
        from datetime import datetime, timezone
        role = self._app.app_properties_.role_
        mode = self._app.runner_.mode_
        manifest_version = self._app.manifest_.manifest_version_
        start_dt = self._app.app_trace_._start_trace_date_time
        stop_dt = self._app.app_trace_._stop_trace_date_time
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': self._status if self._status is not None else 'unknown',
            'role': role,
            'mode': mode,
            'version': manifest_version,
            'start': start_dt.isoformat() if start_dt is not None else None,
            'stop': stop_dt.isoformat() if stop_dt is not None else None,
        }


```

### platform/shell/component/runtime/__init__.py
```
from shell.component.runtime.runtime.runtime import Runtime
```

### platform/shell/component/runtime/runtime/__init__.py
```
from shell.component.runtime.runtime.runtime import Runtime
```

### platform/shell/component/runtime/runtime/internal/_init_manifest.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.component.runtime.runtime.runtime import Runtime


def _init_manifest(runtime: Runtime) -> None:
    runtime.manifest_.init_manifest()
```

### platform/shell/component/runtime/runtime/internal/_init_runtime.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

from shell.utils.system.system import System
from shell.component.runtime.runtime.internal._init_manifest import _init_manifest
from shell.component.runtime.runtime.internal._init_runtime_config import _init_runtime_config

if TYPE_CHECKING:
    from shell.component.runtime.runtime.runtime import Runtime


def _init_runtime(runtime: Runtime, version_info: tuple[int, ...] | None = None) -> None:
    System().validate(version_info=version_info)
    _init_runtime_config(runtime)
    _init_manifest(runtime)
```

### platform/shell/component/runtime/runtime/internal/_init_runtime_config.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

from shell.constants.constants import CONFIG_DIR, CONFIG_YAML

if TYPE_CHECKING:
    from shell.component.runtime.runtime.runtime import Runtime


def _init_runtime_config(runtime: Runtime) -> None:
    config_path = runtime.app_.cli_.cli_properties_.runner_root_dir_ / CONFIG_DIR / CONFIG_YAML
    runtime.runtime_config_.init_config(config_path, source='runtime')
```

### platform/shell/component/runtime/runtime/runtime.py
```
"""runtime.py
Runtime — container for runtime-level objects shared across the graph run.

Slots:
    _app                — Optional; App instance
    _manifest           — Optional; Manifest instance
    _runtime_config     — Optional; Config instance
    _runtime_properties — Optional; RuntimeProperties instance
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.component.manifest.manifest import Manifest
from shell.component.config.config.config import Config
from shell.component.runtime.runtime_properties.runtime_properties import RuntimeProperties
from shell.component.runtime.runtime.internal._init_runtime import _init_runtime

if TYPE_CHECKING:
    from shell.app.app.app import App


class Runtime:

    __slots__ = ("_app", "_manifest", "_runtime_config", "_runtime_properties")

    def __init__(self) -> None:
        self._app: App | None = None
        self._manifest: Manifest | None = None
        self._runtime_config: Config | None = None
        self._runtime_properties: RuntimeProperties | None = None

    @property
    def app_(self) -> App:
        return self._app

    @property
    def manifest_(self) -> Manifest:
        if self._manifest is None:
            self._manifest = Manifest(self._app)
        return self._manifest

    @property
    def runtime_config_(self) -> Config:
        if self._runtime_config is None:
            self._runtime_config = Config(self._app)
        return self._runtime_config

    @property
    def runtime_properties_(self) -> RuntimeProperties:
        if self._runtime_properties is None:
            self._runtime_properties = RuntimeProperties(self)
        return self._runtime_properties

    def init_runtime(self, version_info: tuple[int, ...] | None = None) -> None:
        _init_runtime(self, version_info=version_info)

```

### platform/shell/component/runtime/runtime.md
```
Modul glowny runtime

Grupuje klasy odpowiedzialne za informacje dotyczace aktualnie uruchomionemu runtimowi
to co jest w katalogu z ktorego runtime jest fizycznie uruchomiony czyli , nazwa pliku wykonywalnego
polozenie pliku wykonywalnego, manifest oraz defoltowy config z podstawowymi parametrami
```

### platform/shell/component/runtime/runtime_properties/__init__.py
```
from shell.component.runtime.runtime_properties.runtime_properties import RuntimeProperties
```

### platform/shell/component/runtime/runtime_properties/internal/__init__.py
```
```

### platform/shell/component/runtime/runtime_properties/internal/_assert_runtime_properties_loaded.py
```
def _assert_runtime_properties_loaded(name: str | None) -> None:
    if name is None:
        raise ValueError("[RuntimeProperties] not loaded — call init_runtime() first")
```

### platform/shell/component/runtime/runtime_properties/runtime_properties.py
```
"""runtime_properties.py
RuntimeProperties — typed accessors for runtime's config.yaml values.

Slots:
    _runtime — parent Runtime
"""

from __future__ import annotations

from shell.component.runtime.runtime_properties.internal._assert_runtime_properties_loaded import _assert_runtime_properties_loaded


class RuntimeProperties:

    __slots__ = ("_runtime",)

    def __init__(self, runtime) -> None:
        self._runtime = runtime

    @property
    def name_(self) -> str:
        value = self._runtime.runtime_config_.config_dict_.get('name')
        _assert_runtime_properties_loaded(value)
        return value

    @property
    def mode_(self) -> str | None:
        return self._runtime.runtime_config_.config_dict_.get('mode')

    @property
    def role_(self) -> str | None:
        return self._runtime.runtime_config_.config_dict_.get('role')

    @property
    def type_(self) -> str | None:
        return self._runtime.runtime_config_.config_dict_.get('type')

    @property
    def model_(self) -> str | None:
        return self._runtime.runtime_config_.config_dict_.get('model')

    @property
    def command_(self) -> str | None:
        return self._runtime.runtime_config_.config_dict_.get('command')

    @property
    def runner_root_dir_(self) -> str | None:
        return self._runtime.runtime_config_.config_dict_.get('runner_root_dir')

    @property
    def script_name_(self) -> str | None:
        return self._runtime.runtime_config_.config_dict_.get('script_name')

    @property
    def work_dir_(self) -> str | None:
        return self._runtime.runtime_config_.config_dict_.get('work_dir')

    @property
    def timeout_(self) -> int | None:
        return self._runtime.runtime_config_.config_dict_.get('timeout')

    @property
    def retries_(self) -> int | None:
        return self._runtime.runtime_config_.config_dict_.get('retries')

    @property
    def log_level_(self) -> str | None:
        return self._runtime.runtime_config_.config_dict_.get('log_level')

    @property
    def max_step_(self) -> int | None:
        return self._runtime.runtime_config_.config_dict_.get('max_step')

    @property
    def no_ask_user_(self) -> bool | None:
        return self._runtime.runtime_config_.config_dict_.get('no_ask_user')

    @property
    def autopilot_(self) -> bool | None:
        return self._runtime.runtime_config_.config_dict_.get('autopilot')
```

### platform/shell/constants/__init__.py
```
```

### platform/shell/constants/constants.py
```
CONFIG_DIR = 'config'
CONFIG_YAML = 'config.yaml'
MANIFEST_YAML = 'manifest.yaml'

DOT_NODE = '.node'

DIR_INPUT = 'input'
DIR_OUTPUT = 'output'
DIR_LOGS = 'logs'
DIR_TEMP = 'temp'
DIR_ARCHIVE = 'archive'
DIR_SCRIPTS = 'scripts'
DIR_PROMPT = 'prompt'
DIR_STAGE = 'stage'
DIR_TASK = 'task'

DIR_STAGE_ACTIVE = 'active'
DIR_STAGE_PENDING = 'pending'
DIR_STAGE_HISTORY = 'history'
DIR_STAGE_IGNORED = 'ignored'
DIR_STAGE_DEAD = 'dead'
DIR_STAGE_DONE = 'done'
```

### platform/shell/context/__init__.py
```
```

### platform/shell/context/audit_context/__init__.py
```
```

### platform/shell/context/audit_context/audit_context/__init__.py
```
```

### platform/shell/context/audit_context/audit_context/audit_context.py
```
"""audit_context.py
AuditContext — audit and traceability context for process reconstruction.

Slots:
    _request_id — unique request identifier
    _user       — user or agent that initiated the request
    _timestamp  — ISO 8601 timestamp of the request
    _trace_id   — distributed trace identifier
"""

from __future__ import annotations

from shell.context.audit_context.audit_context.internal._init_audit_context import _init_audit_context


class AuditContext:
    """Audit and traceability context.

    Slots:
        _request_id — unique request identifier
        _user       — user or agent that initiated the request
        _timestamp  — ISO 8601 timestamp of the request
        _trace_id   — distributed trace identifier
    """

    __slots__ = ("_request_id", "_user", "_timestamp", "_trace_id")

    def __init__(self) -> None:
        self._request_id: str = ""
        self._user: str = ""
        self._timestamp: str = ""
        self._trace_id: str = ""

    @property
    def request_id_(self) -> str:
        return self._request_id

    @property
    def user_(self) -> str:
        return self._user

    @property
    def timestamp_(self) -> str:
        return self._timestamp

    @property
    def trace_id_(self) -> str:
        return self._trace_id

    def init_audit_context(self) -> None:
        _init_audit_context(self)
```

### platform/shell/context/audit_context/audit_context/internal/__init__.py
```
```

### platform/shell/context/audit_context/audit_context/internal/_init_audit_context.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.context.audit_context.audit_context.audit_context import AuditContext


def _init_audit_context(audit_context: AuditContext) -> None:
    audit_context._request_id = ""
    audit_context._user = ""
    audit_context._timestamp = ""
    audit_context._trace_id = ""
```

### platform/shell/context/communication_context/__init__.py
```
```

### platform/shell/context/communication_context/communication_context/__init__.py
```
```

### platform/shell/context/communication_context/communication_context/communication_context.py
```
"""communication_context.py
CommunicationContext — inter-agent communication context.

Slots:
    _sender          — identifier of the sending agent
    _receiver        — identifier of the receiving agent
    _correlation_id  — correlation ID linking delegations in a conversation
    _previous_messages — list of previous messages in this conversation
"""

from __future__ import annotations

from shell.context.communication_context.communication_context.internal._init_communication_context import _init_communication_context


class CommunicationContext:
    """Inter-agent communication context.

    Slots:
        _sender          — identifier of the sending agent
        _receiver        — identifier of the receiving agent
        _correlation_id  — correlation ID linking delegations in a conversation
        _previous_messages — list of previous messages in this conversation
    """

    __slots__ = ("_sender", "_receiver", "_correlation_id", "_previous_messages")

    def __init__(self) -> None:
        self._sender: str = ""
        self._receiver: str = ""
        self._correlation_id: str = ""
        self._previous_messages: list[dict] = []

    @property
    def sender_(self) -> str:
        return self._sender

    @property
    def receiver_(self) -> str:
        return self._receiver

    @property
    def correlation_id_(self) -> str:
        return self._correlation_id

    @property
    def previous_messages_(self) -> list[dict]:
        return self._previous_messages

    def init_communication_context(self, sender: str, receiver: str, correlation_id: str = "") -> None:
        _init_communication_context(self, sender=sender, receiver=receiver, correlation_id=correlation_id)
```

### platform/shell/context/communication_context/communication_context/internal/__init__.py
```
```

### platform/shell/context/communication_context/communication_context/internal/_init_communication_context.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.context.communication_context.communication_context.communication_context import CommunicationContext


def _init_communication_context(
    communication_context: CommunicationContext,
    sender: str,
    receiver: str,
    correlation_id: str = "",
) -> None:
    communication_context._sender = sender
    communication_context._receiver = receiver
    communication_context._correlation_id = correlation_id
    communication_context._previous_messages = []
```

### platform/shell/context/context/__init__.py
```
```

### platform/shell/context/context/context.py
```
"""context.py
Context — execution context passed to internal functions.

Slots:
"""

from __future__ import annotations

from shell.context.context.internal._init_context import _init_context


class Context:
    """Execution context.

    Slots:
    """

    __slots__ = ()

    def __init__(self) -> None:
        pass

    def init_context(self) -> None:
        _init_context(self)
```

### platform/shell/context/context/internal/__init__.py
```
```

### platform/shell/context/context/internal/_init_context.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.context.context.context import Context


def _init_context(context: Context) -> None:
    pass
```

### platform/shell/context/context.md
```
Ma struktura ma zawierac i przekazywac caly kontekst dla dowolnego node
zarowno komendy jak i prompty zbudowane w dowolny sposob
Kontekst ma zawierac komplet informacji ktore agent potrzebuje by poprawnie realizowac zadanie
Jest podreczna biblioteka najwazniejszych niezbednych elementow ktore agent musi znac
Podzial bedzie

a)system context - to beda wszystkie reguly sterujace agenta, to by agent wiedzial co moze czego nie moze
  z kim moze sie komunikowac co ma w dyspozycji systemowej jakie narzedzia i technologie,
  tu jest okreslana rola agenta i powiazane z nia skille
b)domain contekst to jest zbior informacji o domenie w ktorej agent sie porusza wiedza z czym ogolnie ma doczynienia
c)session contekst to kontekst zwiazany z sessia calym zadaniem jakie jest realizowane dzieki temu agent dostac moze informacje o czyms co zostalo juz ustalone wczesniej
e)memory_contekst to zbior informacji ktore zostaly ustalone we wczesniejszych procesach sesjach czesto powtarzalnych regolach lub waznych informacjach, tu agent moze siegnac by sie czegos nauczonego o przedmiocie dowiedziec
f) execution_context - kontekst tego subzadania tego co tu i teraz jest do wykonania  




Dla architektury agentowej / graph-based (LangGraph, Semantic Kernel, własny orchestrator) taki podział jest sensowny, ale brakuje jeszcze kilku warstw, które w praktyce bardzo szybko okazują się potrzebne.

Ja rozdzieliłbym to tak:

Context
├── system_context
├── domain_context
├── session_context
├── memory_context
├── execution_context
├── communication_context
├── resource_context
├── state_context
└── audit_context
1. system_context

Stałe reguły działania agenta.

Przykłady:

agent_id: architect-agent

role:
  name: Enterprise Architect

skills:
  - java
  - spring
  - ddd
  - cqrs

constraints:
  - never_modify_production
  - no_external_calls

available_tools:
  - vector_search
  - sql_query
  - github_search

communication_rules:
  - can_call: [analyst-agent, coding-agent]

Odpowiada na pytanie:

Kim jestem i jakie są moje globalne zasady?

2. domain_context

Wiedza domenowa.

Przykład:

domain:
  name: Banking

entities:
  - Customer
  - Account
  - Transaction

business_rules:
  - account_must_have_owner
  - transaction_cannot_be_negative

Odpowiada na pytanie:

W jakim świecie biznesowym działam?

3. session_context

Kontekst całego procesu.

Przykład:

session_id: S-123

goal:
  migrate monolith to microservices

decisions:
  - use kafka
  - use postgres

completed_tasks:
  - identify bounded contexts

Odpowiada na pytanie:

Co już ustaliliśmy w tej konkretnej sesji?

4. memory_context

Długoterminowa pamięć.

Przykład:

lessons_learned:
  - customer_service_should_not_own_payments

organization_preferences:
  - use_java_21
  - use_maven

known_patterns:
  - event_sourcing
  - outbox_pattern

Odpowiada na pytanie:

Czego nauczyłem się wcześniej?

5. execution_context

Najważniejszy dla pojedynczego node.

Przykład:

task:
  generate_rest_api

input:
  aggregate: Customer

expected_output:
  openapi_spec

constraints:
  - use_rest
  - no_graphql

Odpowiada na pytanie:

Co mam zrobić dokładnie teraz?

Brakuje jeszcze:
6. communication_context

Przy multi-agentach jest krytyczny.

Przykład:

sender:
  analyst-agent

receiver:
  architect-agent

conversation:
  correlation_id: XYZ

previous_messages:
  - ...

Odpowiada na pytanie:

Kto mi to zlecił i z jakim kontekstem komunikacyjnym?

Bez tego ciężko śledzić delegacje między agentami.

7. resource_context

Źródła wiedzy dostępne dla agenta.

Przykład:

documents:
  - ADR-001
  - ADR-002

repositories:
  - customer-service

knowledge_sources:
  - vector_db
  - wiki

Odpowiada na pytanie:

Z jakich danych mogę korzystać?

To nie jest domain context.

Domain opisuje świat biznesowy.

Resource opisuje skąd agent ma pobierać wiedzę.

8. state_context

Stan workflow.

Przykład:

workflow:
  id: WF-22

current_node:
  architecture-review

previous_node:
  requirements-analysis

next_node:
  implementation

Odpowiada na pytanie:

Gdzie jestem w grafie procesu?

Przy LangGraphach i własnych orchestratorach to zwykle osobna sekcja.

9. audit_context

Enterprise'owo bardzo przydatne.

Przykład:

request_id: R-123

user:
  john.smith

timestamp:
  2026-05-31T10:00:00

trace_id:
  abc-xyz

Odpowiada na pytanie:

Jak odtworzyć wykonanie procesu?

Finalnie

Gdybym projektował uniwersalny AgentContext dla enterprise multi-agent system, zrobiłbym:

AgentContext
 ├─ SystemContext
 ├─ DomainContext
 ├─ SessionContext
 ├─ MemoryContext
 ├─ ExecutionContext
 ├─ CommunicationContext
 ├─ ResourceContext
 ├─ StateContext
 └─ AuditContext

Przy czym dla pojedynczego node najważniejsze są zwykle:

SystemContext
+
ExecutionContext
+
SessionContext
+
MemoryContext

a pozostałe pełnią rolę infrastrukturalną i orkiestracyjną. To daje praktycznie kompletny model kontekstu dla agentów enterprise działających w grafach, workflow i architekturach multi-agent.
```

### platform/shell/context/domain_context/__init__.py
```
```

### platform/shell/context/domain_context/domain_context/__init__.py
```
```

### platform/shell/context/domain_context/domain_context/domain_context.py
```
"""domain_context.py
DomainContext — domain-level execution context.

Slots:
"""

from __future__ import annotations

from shell.context.domain_context.domain_context.internal._init_domain_context import _init_domain_context


class DomainContext:
    """Domain-level execution context.

    Slots:
    """

    __slots__ = ()

    def __init__(self) -> None:
        pass

    def init_domain_context(self) -> None:
        _init_domain_context(self)
```

### platform/shell/context/domain_context/domain_context/internal/__init__.py
```
```

### platform/shell/context/domain_context/domain_context/internal/_init_domain_context.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.context.domain_context.domain_context.domain_context import DomainContext


def _init_domain_context(domain_context: DomainContext) -> None:
    pass
```

### platform/shell/context/domain_context/domain_context.md
```
kontekst domeny to kontekst z jaka domena technologiczna biznesowa agent ma pracowac
```

### platform/shell/context/execution_context/__init__.py
```
```

### platform/shell/context/execution_context/execution_context/__init__.py
```
```

### platform/shell/context/execution_context/execution_context/execution_context.py
```
"""execution_context.py
ExecutionContext — sub-task execution context: what to do right now.

Slots:
    _task        — name of the task to execute
    _input       — input data for the task
    _expected_output — description of expected output
    _constraints — list of constraints for this execution
"""

from __future__ import annotations

from shell.context.execution_context.execution_context.internal._init_execution_context import _init_execution_context


class ExecutionContext:
    """Sub-task execution context.

    Slots:
        _task            — name of the task to execute
        _input           — input data for the task
        _expected_output — description of expected output
        _constraints     — list of constraints for this execution
    """

    __slots__ = ("_task", "_input", "_expected_output", "_constraints")

    def __init__(self) -> None:
        self._task: str = ""
        self._input: dict = {}
        self._expected_output: str = ""
        self._constraints: list[str] = []

    @property
    def task_(self) -> str:
        return self._task

    @property
    def input_(self) -> dict:
        return self._input

    @property
    def expected_output_(self) -> str:
        return self._expected_output

    @property
    def constraints_(self) -> list[str]:
        return self._constraints

    def init_execution_context(self) -> None:
        _init_execution_context(self)
```

### platform/shell/context/execution_context/execution_context/internal/__init__.py
```
```

### platform/shell/context/execution_context/execution_context/internal/_init_execution_context.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.context.execution_context.execution_context.execution_context import ExecutionContext


def _init_execution_context(execution_context: ExecutionContext) -> None:
    execution_context._task = ""
    execution_context._input = {}
    execution_context._expected_output = ""
    execution_context._constraints = []
```

### platform/shell/context/memory_context/__init__.py
```
```

### platform/shell/context/memory_context/memory_context/__init__.py
```
```

### platform/shell/context/memory_context/memory_context/internal/__init__.py
```
```

### platform/shell/context/memory_context/memory_context/internal/_init_memory_context.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.context.memory_context.memory_context.memory_context import MemoryContext


def _init_memory_context(memory_context: MemoryContext) -> None:
    memory_context._lessons_learned = []
    memory_context._organization_preferences = []
    memory_context._known_patterns = []
```

### platform/shell/context/memory_context/memory_context/memory_context.py
```
"""memory_context.py
MemoryContext — long-term memory context: lessons learned, preferences, known patterns.

Slots:
    _lessons_learned         — list of lessons learned from previous processes
    _organization_preferences — list of organization-level preferences
    _known_patterns          — list of known architectural or process patterns
"""

from __future__ import annotations

from shell.context.memory_context.memory_context.internal._init_memory_context import _init_memory_context


class MemoryContext:
    """Long-term memory context.

    Slots:
        _lessons_learned          — list of lessons learned from previous processes
        _organization_preferences — list of organization-level preferences
        _known_patterns           — list of known architectural or process patterns
    """

    __slots__ = ("_lessons_learned", "_organization_preferences", "_known_patterns")

    def __init__(self) -> None:
        self._lessons_learned: list[str] = []
        self._organization_preferences: list[str] = []
        self._known_patterns: list[str] = []

    @property
    def lessons_learned_(self) -> list[str]:
        return self._lessons_learned

    @property
    def organization_preferences_(self) -> list[str]:
        return self._organization_preferences

    @property
    def known_patterns_(self) -> list[str]:
        return self._known_patterns

    def init_memory_context(self) -> None:
        _init_memory_context(self)
```

### platform/shell/context/session_context/__init__.py
```
```

### platform/shell/context/session_context/session_context/__init__.py
```
```

### platform/shell/context/session_context/session_context/internal/__init__.py
```
```

### platform/shell/context/session_context/session_context/internal/_init_session_context.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.context.session_context.session_context.session_context import SessionContext


def _init_session_context(session_context: SessionContext) -> None:
    pass
```

### platform/shell/context/session_context/session_context/session_context.py
```
"""session_context.py
SessionContext — session-level execution context.

Slots:
"""

from __future__ import annotations

from shell.context.session_context.session_context.internal._init_session_context import _init_session_context


class SessionContext:
    """Session-level execution context.

    Slots:
    """

    __slots__ = ()

    def __init__(self) -> None:
        pass

    def init_session_context(self) -> None:
        _init_session_context(self)
```

### platform/shell/context/session_context/session_context.md
```
to zbior danych ktore agent zgromadzil w sesji ktore moga byc dla niego istotne w dalszej pracy
```

### platform/shell/context/state_context/__init__.py
```
```

### platform/shell/context/state_context/state_context/__init__.py
```
```

### platform/shell/context/state_context/state_context/internal/__init__.py
```
```

### platform/shell/context/state_context/state_context/internal/_init_state_context.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.context.state_context.state_context.state_context import StateContext


def _init_state_context(state_context: StateContext) -> None:
    state_context._workflow_id = ""
    state_context._current_node = ""
    state_context._previous_node = ""
    state_context._next_node = ""
```

### platform/shell/context/state_context/state_context/state_context.py
```
"""state_context.py
StateContext — workflow state context: current position in the process graph.

Slots:
    _workflow_id   — identifier of the workflow
    _current_node  — name of the currently executing node
    _previous_node — name of the previously executed node
    _next_node     — name of the next node to execute
"""

from __future__ import annotations

from shell.context.state_context.state_context.internal._init_state_context import _init_state_context


class StateContext:
    """Workflow state context.

    Slots:
        _workflow_id   — identifier of the workflow
        _current_node  — name of the currently executing node
        _previous_node — name of the previously executed node
        _next_node     — name of the next node to execute
    """

    __slots__ = ("_workflow_id", "_current_node", "_previous_node", "_next_node")

    def __init__(self) -> None:
        self._workflow_id: str = ""
        self._current_node: str = ""
        self._previous_node: str = ""
        self._next_node: str = ""

    @property
    def workflow_id_(self) -> str:
        return self._workflow_id

    @property
    def current_node_(self) -> str:
        return self._current_node

    @property
    def previous_node_(self) -> str:
        return self._previous_node

    @property
    def next_node_(self) -> str:
        return self._next_node

    def init_state_context(self) -> None:
        _init_state_context(self)
```

### platform/shell/context/system_context/__init__.py
```
```

### platform/shell/context/system_context/system_context/__init__.py
```
```

### platform/shell/context/system_context/system_context/internal/__init__.py
```
```

### platform/shell/context/system_context/system_context/internal/_init_system_context.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.context.system_context.system_context.system_context import SystemContext


def _init_system_context(system_context: SystemContext) -> None:
    pass
```

### platform/shell/context/system_context/system_context/system_context.py
```
"""system_context.py
SystemContext — system-level execution context.

Slots:
"""

from __future__ import annotations

from shell.context.system_context.system_context.internal._init_system_context import _init_system_context


class SystemContext:
    """System-level execution context.

    Slots:
    """

    __slots__ = ()

    def __init__(self) -> None:
        pass

    def init_system_context(self) -> None:
        _init_system_context(self)
```

### platform/shell/context/system_context/system_context.md
```
system contekst to promppt sterujace prompty informujace o roli agenta i jego kozliwosciach technicznych i konfiguracyjnych
```

### platform/shell/dirmode.md
```
# Architektura DOM

Struktura oparta na drzewie obiektów, którego korzeniem jest klasa `App`.
Umożliwia dostęp do dowolnego obiektu z dowolnego miejsca poprzez korzeń drzewa.

## Zasady budowy klas

- Każda klasa posiada slot `_app` — referencja do korzenia drzewa (`App`).
- Każda klasa posiada metodę `init_<nazwa>()` — główny konstruktor inicjalizujący obiekt po jego utworzeniu.
- Konstruktor `__init__` tylko zeruje sloty do `None`; nie zawiera logiki inicjalizacyjnej.
- Obiekty podrzędne tworzone są lazy w property — property tworzy pusty obiekt z przekazanym `_app`.

## Nawigacja w drzewie

- Do góry: przez slot `_app` (zawsze dostępny).
- W dół: przez property z lazy loadingiem.
- Gdy klasa występuje jako element listy lub słownika, posiada dodatkowo slot z referencją do swojego bezpośredniego rodzica — adresacja w obie strony.

```

### platform/shell/docs/opis_platformy.md
```
Jak używać Memory
1. Inicjalizacja
Aby przejść na inną bazę — wstrzykujesz inny driver, np. PostgresDriver(dsn) (gdy stub zostanie dokończony). Reszta kodu się nie zmienia.

2. Context entries (klucz–wartość per scope)
context_type to typ kontekstu (system, domain, session, memory, state, audit, execution, communication).

3. Sesje agentów
4. Konwersacje (komunikacja między agentami)
5. Audit log
6. RAG (przez memory.rag_)
7. Zamknięcie
Ścieżka skrótu — gdzie co siedzi
memory.put_entry/get_entry/... — context_entry (UPSERT po (context_type, scope_id, entry_key))
memory.open_session/close_session — tabela session
memory.append_message/get_conversation — tabela message (po correlation_id)
memory.log_event — tabela audit_event
memory.rag_.index_text — tabele rag_document + rag_chunk (+ rag_chunk_fts na sqlite)
memory.rag_.search — kosinusowe podobieństwo embeddingów w Pythonie
memory.backend_.search_fts — BM25 przez FTS5
Aby podpiąć prawdziwe embeddingi (np. OpenAI / sentence-transformers) — zaimplementuj Embedder (jeden metod encode(text) -> list[float]) zamiast HashEmbedder.
```

### platform/shell/logger/__init__.py
```
# lib/logger package
from shell.logger.logger import Logger

__all__ = ["Logger"]
```

### platform/shell/logger/internal/__init__.py
```
```

### platform/shell/logger/internal/_build_log_path.py
```
from shell.utils.path.path import PathType
"""_build_log_path.py
Responsible for one thing: building the log file path inside the node logs/ directory.
Convention: logs/<role>.<YYYY-MM-DD_HH>.<level>.log_
"""

from datetime import datetime, timezone


def _build_log_path(node: PathType, log_level: str = "INFO", now: datetime = None, role: str = "agent") -> PathType:
    """Return logs/<role>.<YYYY-MM-DD_HH>.<level>.log_ inside node."""
    if now is None:
        now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%d_%H")
    return node / ".node" / "logs" / f"{role}.{stamp}.{log_level.strip().lower()}.log"
```

### platform/shell/logger/internal/_get_logger.py
```
"""_get_logger.py
Private. Responsible for one thing: providing a configured logger
that writes to a log file (configured level) and stderr (WARNING+).

Log format: timestamp | level | message
"""

from __future__ import annotations

from shell.utils.path.path import PathType


import logging
from collections.abc import Callable

from shell.utils.io.io import default_file_handler, default_make_dirs
from shell.logger.internal._build_log_path import _build_log_path
from shell.logger.internal._make_formatter import _make_formatter
from shell.logger.internal._resolve_level import _resolve_level


def _get_logger(app, make_dirs: Callable[[PathType], None] | None = None, make_file_handler: Callable[[PathType], logging.FileHandler] | None = None) -> logging.Logger:
    """Return an isolated logger writing to a log file and stderr.

    On first call builds and configures the logger, then caches it on the Logger facade.
    Subsequent calls return the cached instance directly.
    make_dirs:         optional callable (path: PathType) -> None (defaults to mkdir with parents).
    make_file_handler: optional callable (path: PathType) -> logging.FileHandler.
    """
    logger = app.app_trace_.logger_
    if logger.cached_logger_ is not None:
        return logger.cached_logger_

    if make_dirs is None:
        make_dirs = default_make_dirs
    if make_file_handler is None:
        make_file_handler = default_file_handler

    node_dir = app.app_node_.node_.node_dir_
    log_level: str = logger._log_level or 'INFO'
    role: str = app.app_properties_.role_ or app.cli_.cli_properties_.task_name_ or 'unknown'
    log_path = _build_log_path(node_dir, log_level, role=role)
    level_int = _resolve_level(log_level)

    make_dirs(log_path.parent)
    logging_logger = logging.getLogger(str(log_path))
    logging_logger.setLevel(level_int)
    logging_logger.propagate = False

    fmt = _make_formatter()
    fh = make_file_handler(log_path)
    fh.setLevel(level_int)
    fh.setFormatter(fmt)

    sh = logging.StreamHandler()
    sh.setLevel(logging.WARNING)
    sh.setFormatter(fmt)

    logging_logger.addHandler(fh)
    logging_logger.addHandler(sh)
    logger.cached_logger_ = logging_logger
    app.app_trace_.record_info('logger._get_logger._get_logger', f'log file {log_path}')
    return logging_logger
```

### platform/shell/logger/internal/_make_formatter.py
```
"""_make_formatter.py
Responsible for one thing: creating the shared log formatter.

Format: timestamp | level | message
"""

import logging
from datetime import datetime, timezone


class IsoUtcFormatter(logging.Formatter):
    """Formatter that emits ISO8601 UTC timestamps with milliseconds."""

    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        # e.g. 2026-05-01T06:54:17.326Z
        return dt.isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def _make_formatter() -> logging.Formatter:
    return IsoUtcFormatter("%(asctime)s | %(levelname)-8s | %(message)s")
```

### platform/shell/logger/internal/_resolve_level.py
```
"""_resolve_level.py
Private. Responsible for one thing: converting a log-level name string
(e.g. 'DEBUG', 'info') to the corresponding logging integer constant.
"""

import logging


def _resolve_level(level_name: str) -> int:
    """Return the logging int for level_name; defaults to INFO for unknown values."""
    return getattr(logging, str(level_name).strip().upper(), logging.INFO)
```

### platform/shell/logger/logger.md
```
Modul loggera udostepnia metody loggujace odbiorca jego metod jest modul trace poniewaz on jest akumulatorem loggera
```

### platform/shell/logger/logger.py
```
"""logger.py
Logger: single-entry-point facade over the underlying logging.Logger.

Consolidates all structured log operations for a node run:
    info()    — informational message
    error()   — error message (does not change status or raise)
    warning() — warning message (does not change status or raise)
"""

from __future__ import annotations

import logging

from shell.logger.internal._get_logger import _get_logger


class Logger:
    """Structured logger for a single node run.

    Wraps the underlying logging.Logger (built and cached by _get_logger)
    and provides domain-aware methods that can mutate app status.

    The underlying logger is lazily resolved on first use through _get_logger,
    which caches the result on app — so Logger(app) is cheap to construct.
    """

    __slots__ = ("_app", "_log_level", "_cached_logger")

    def __init__(self, app) -> None:
        self._app = app
        self._log_level: str | None = None
        self._cached_logger: logging.Logger | None = None

    # -----------------------------------------------------------------------
    # Validated property
    # -----------------------------------------------------------------------

    @property
    def log_level_(self) -> str:
        """Return log_level. Raises if not set."""
        if not self._log_level:
            raise ValueError("[Logger] log_level is not set")
        return self._log_level

    @property
    def cached_logger_(self) -> logging.Logger | None:
        return self._cached_logger

    @cached_logger_.setter
    def cached_logger_(self, value: logging.Logger) -> None:
        self._cached_logger = value

    # ------------------------------------------------------------------ #
    # Logging methods                                                      #
    # ------------------------------------------------------------------ #

    def info(self, message: str) -> None:
        """Log an info message."""
        _get_logger(self._app).info(message)

    def error(self, message: str, exc_info: bool = False) -> None:
        """Log an error message. Does not change status or raise."""
        _get_logger(self._app).error(message, exc_info=exc_info)

    def warning(self, message: str) -> None:
        """Log a warning message. Does not change status or raise."""
        _get_logger(self._app).warning(message)
```

### platform/shell/memory/__init__.py
```
```

### platform/shell/memory/memory/__init__.py
```
```

### platform/shell/memory/memory/internal/__init__.py
```
```

### platform/shell/memory/memory/internal/_init_memory.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

from shell.memory.rag_index.rag_index import RagIndex
from shell.memory.rag_index.embedder.hash_embedder import HashEmbedder

if TYPE_CHECKING:
    from shell.memory.memory.memory import Memory
    from shell.memory.memory_backend.memory_backend import MemoryBackend
    from shell.memory.rag_index.embedder.embedder import Embedder


def _init_memory(memory: Memory, backend: MemoryBackend, embedder: Embedder | None) -> None:
    backend.init_backend()
    memory._backend = backend
    memory._rag = RagIndex(backend, embedder if embedder is not None else HashEmbedder())
```

### platform/shell/memory/memory/memory.py
```
"""memory.py
Memory — facade exposing the persistent context store and RAG index.

Slots:
    _backend  — Optional; MemoryBackend instance (None until init_memory)
    _rag      — Optional; RagIndex instance (None until init_memory)
"""

from __future__ import annotations

from shell.memory.memory_backend.memory_backend import MemoryBackend
from shell.memory.rag_index.embedder.embedder import Embedder
from shell.memory.rag_index.rag_index import RagIndex
from shell.memory.memory.internal._init_memory import _init_memory


class Memory:
    """Facade exposing the persistent context store and RAG index.

    Slots:
        _backend  — Optional; MemoryBackend instance (None until init_memory)
        _rag      — Optional; RagIndex instance (None until init_memory)
    """

    __slots__ = ("_backend", "_rag")

    def __init__(self) -> None:
        self._backend: MemoryBackend | None = None
        self._rag: RagIndex | None = None

    @property
    def backend_(self) -> MemoryBackend:
        return self._backend

    @property
    def rag_(self) -> RagIndex:
        return self._rag

    def init_memory(self, backend: MemoryBackend, embedder: Embedder | None = None) -> None:
        _init_memory(self, backend, embedder)

    def close_memory(self) -> None:
        if self._backend is not None:
            self._backend.close_backend()

    def put_entry(self, context_type: str, scope_id: str, entry_key: str, value: dict, tags: list[str] | None = None) -> None:
        self._backend.put_entry(context_type, scope_id, entry_key, value, tags)

    def get_entry(self, context_type: str, scope_id: str, entry_key: str) -> dict | None:
        return self._backend.get_entry(context_type, scope_id, entry_key)

    def list_entries(self, context_type: str, scope_id: str) -> list[dict]:
        return self._backend.list_entries(context_type, scope_id)

    def delete_entry(self, context_type: str, scope_id: str, entry_key: str) -> None:
        self._backend.delete_entry(context_type, scope_id, entry_key)

    def open_session(self, session_id: str, agent_id: str, goal: str) -> None:
        self._backend.open_session(session_id, agent_id, goal)

    def close_session(self, session_id: str, status: str) -> None:
        self._backend.close_session(session_id, status)

    def append_message(self, correlation_id: str, sender: str, receiver: str, payload: dict) -> None:
        self._backend.append_message(correlation_id, sender, receiver, payload)

    def get_conversation(self, correlation_id: str) -> list[dict]:
        return self._backend.get_conversation(correlation_id)

    def log_event(self, request_id: str, event_type: str, payload: dict, trace_id: str | None = None, user: str | None = None) -> None:
        self._backend.log_event(request_id, event_type, payload, trace_id, user)

```

### platform/shell/memory/memory_backend/__init__.py
```
```

### platform/shell/memory/memory_backend/memory_backend.py
```
"""memory_backend.py
MemoryBackend — abstract interface for persistent memory storage backends.

Slots:
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class MemoryBackend(ABC):
    """Abstract base for memory storage backends.

    Implementations: SqlMemoryBackend (SqliteDriver default; PostgresDriver stub), future: Chroma, Qdrant.
    """

    __slots__ = ()

    @abstractmethod
    def init_backend(self) -> None:
        ...

    @abstractmethod
    def close_backend(self) -> None:
        ...

    @abstractmethod
    def put_entry(self, context_type: str, scope_id: str, entry_key: str, value: dict, tags: list[str] | None = None) -> None:
        ...

    @abstractmethod
    def get_entry(self, context_type: str, scope_id: str, entry_key: str) -> dict | None:
        ...

    @abstractmethod
    def list_entries(self, context_type: str, scope_id: str) -> list[dict]:
        ...

    @abstractmethod
    def delete_entry(self, context_type: str, scope_id: str, entry_key: str) -> None:
        ...

    @abstractmethod
    def open_session(self, session_id: str, agent_id: str, goal: str) -> None:
        ...

    @abstractmethod
    def close_session(self, session_id: str, status: str) -> None:
        ...

    @abstractmethod
    def append_message(self, correlation_id: str, sender: str, receiver: str, payload: dict) -> None:
        ...

    @abstractmethod
    def get_conversation(self, correlation_id: str) -> list[dict]:
        ...

    @abstractmethod
    def log_event(self, request_id: str, event_type: str, payload: dict, trace_id: str | None = None, user: str | None = None) -> None:
        ...

    @abstractmethod
    def index_document(self, source_uri: str, title: str, domain: str, chunks: list[str], embeddings: list[bytes], embedding_model: str) -> int:
        ...

    @abstractmethod
    def search_rag(self, query_embedding: bytes, top_k: int = 5, domain: str | None = None) -> list[dict]:
        ...

    @abstractmethod
    def search_fts(self, query_text: str, top_k: int = 5) -> list[dict]:
        ...
```

### platform/shell/memory/rag_index/__init__.py
```
```

### platform/shell/memory/rag_index/embedder/__init__.py
```
```

### platform/shell/memory/rag_index/embedder/embedder.py
```
"""embedder.py
Embedder — abstract interface for text embedding providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Embedder(ABC):
    """Abstract base for embedding providers (sentence-transformers, OpenAI, Ollama)."""

    __slots__ = ()

    @property
    @abstractmethod
    def model_name_(self) -> str:
        ...

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        ...

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        ...
```

### platform/shell/memory/rag_index/embedder/hash_embedder.py
```
"""hash_embedder.py
HashEmbedder — deterministic, no-dependency stub embedder for tests/dev.

Generates a fixed-dim float vector from the text via hashing — useful as a
default plug while a real model (sentence-transformers / Ollama) is wired in.
"""

from __future__ import annotations

import hashlib
import math
import struct

from shell.memory.rag_index.embedder.embedder import Embedder


class HashEmbedder(Embedder):
    """Deterministic hash-based embedder (dev/test only)."""

    __slots__ = ("_dim", "_model_name")

    def __init__(self, dim: int = 64) -> None:
        self._dim: int = dim
        self._model_name: str = f"hash-stub-{dim}"

    @property
    def model_name_(self) -> str:
        return self._model_name

    @property
    def dim_(self) -> int:
        return self._dim

    def embed_text(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        repeats = (self._dim * 4 + len(digest) - 1) // len(digest)
        raw = (digest * repeats)[: self._dim * 4]
        ints = struct.unpack(f"{self._dim}I", raw)
        floats = [(v / 0xFFFFFFFF) * 2.0 - 1.0 for v in ints]
        norm = math.sqrt(sum(x * x for x in floats)) or 1.0
        return [x / norm for x in floats]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]
```

### platform/shell/memory/rag_index/internal/__init__.py
```
```

### platform/shell/memory/rag_index/internal/_chunk_text.py
```
from __future__ import annotations


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("[RagIndex._chunk_text] chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("[RagIndex._chunk_text] overlap must be in [0, chunk_size)")
    text = text.strip()
    if not text:
        return []
    chunks: list[str] = []
    step = chunk_size - overlap
    for start in range(0, len(text), step):
        chunk = text[start:start + chunk_size]
        if not chunk:
            break
        chunks.append(chunk)
        if start + chunk_size >= len(text):
            break
    return chunks
```

### platform/shell/memory/rag_index/internal/_encode_vector.py
```
from __future__ import annotations

import struct


def _encode_vector(vector: list[float]) -> bytes:
    return struct.pack(f"{len(vector)}f", *vector)
```

### platform/shell/memory/rag_index/internal/_index_text.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

from shell.memory.rag_index.internal._chunk_text import _chunk_text
from shell.memory.rag_index.internal._encode_vector import _encode_vector

if TYPE_CHECKING:
    from shell.memory.rag_index.rag_index import RagIndex


def _index_text(
    rag: RagIndex,
    source_uri: str,
    title: str,
    domain: str,
    text: str,
    chunk_size: int,
    overlap: int,
) -> int:
    chunks = _chunk_text(text, chunk_size, overlap)
    if not chunks:
        return 0
    vectors = rag.embedder_.embed_batch(chunks)
    blobs = [_encode_vector(v) for v in vectors]
    rag.backend_.index_document(
        source_uri=source_uri,
        title=title,
        domain=domain,
        chunks=chunks,
        embeddings=blobs,
        embedding_model=rag.embedder_.model_name_,
    )
    return len(chunks)
```

### platform/shell/memory/rag_index/internal/_search.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

from shell.memory.rag_index.internal._encode_vector import _encode_vector

if TYPE_CHECKING:
    from shell.memory.rag_index.rag_index import RagIndex


def _search(rag: RagIndex, query: str, top_k: int, domain: str | None) -> list[dict]:
    query_vector = rag.embedder_.embed_text(query)
    query_blob = _encode_vector(query_vector)
    return rag.backend_.search_rag(query_blob, top_k=top_k, domain=domain)
```

### platform/shell/memory/rag_index/rag_index.py
```
"""rag_index.py
RagIndex — RAG facade: chunk text, embed, persist, retrieve.

Slots:
    _backend  — MemoryBackend instance for persistence
    _embedder — Embedder instance for vector generation
"""

from __future__ import annotations

from shell.memory.memory_backend.memory_backend import MemoryBackend
from shell.memory.rag_index.embedder.embedder import Embedder
from shell.memory.rag_index.internal._chunk_text import _chunk_text
from shell.memory.rag_index.internal._encode_vector import _encode_vector
from shell.memory.rag_index.internal._index_text import _index_text
from shell.memory.rag_index.internal._search import _search


class RagIndex:
    """RAG indexing and retrieval facade.

    Slots:
        _backend  — MemoryBackend instance for persistence
        _embedder — Embedder instance for vector generation
    """

    __slots__ = ("_backend", "_embedder")

    def __init__(self, backend: MemoryBackend, embedder: Embedder) -> None:
        self._backend: MemoryBackend = backend
        self._embedder: Embedder = embedder

    @property
    def backend_(self) -> MemoryBackend:
        return self._backend

    @property
    def embedder_(self) -> Embedder:
        return self._embedder

    def index_text(
        self,
        source_uri: str,
        title: str,
        domain: str,
        text: str,
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> int:
        return _index_text(self, source_uri, title, domain, text, chunk_size, overlap)

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        return _chunk_text(text, chunk_size, overlap)

    def encode_vector(self, vector: list[float]) -> bytes:
        return _encode_vector(vector)

    def search(self, query: str, top_k: int = 5, domain: str | None = None) -> list[dict]:
        return _search(self, query, top_k, domain)
```

### platform/shell/memory/sql_driver/__init__.py
```
```

### platform/shell/memory/sql_driver/dialect.py
```
"""dialect.py
Dialect — value object describing SQL dialect specifics for a SqlDriver.

Slots:
    _placeholder    — placeholder string used by the driver ('?' for sqlite, '%s' for psycopg)
    _auto_pk        — SQL fragment for auto-incrementing integer primary key
    _blob_type      — column type for binary blobs ('BLOB' or 'BYTEA')
    _supports_fts   — whether dialect supports full-text-search on stored data
"""

from __future__ import annotations


class Dialect:
    """SQL dialect descriptor."""

    __slots__ = ("_placeholder", "_auto_pk", "_blob_type", "_supports_fts")

    def __init__(
        self,
        placeholder: str,
        auto_pk: str,
        blob_type: str,
        supports_fts: bool,
    ) -> None:
        self._placeholder: str = placeholder
        self._auto_pk: str = auto_pk
        self._blob_type: str = blob_type
        self._supports_fts: bool = supports_fts

    @property
    def placeholder_(self) -> str:
        return self._placeholder

    @property
    def auto_pk_(self) -> str:
        return self._auto_pk

    @property
    def blob_type_(self) -> str:
        return self._blob_type

    @property
    def supports_fts_(self) -> bool:
        return self._supports_fts

    def render_sql(self, sql: str) -> str:
        if self._placeholder == "?":
            return sql
        out: list[str] = []
        i = 0
        for ch in sql:
            if ch == "?":
                i += 1
                out.append(self._placeholder.replace("$N", str(i)) if "$N" in self._placeholder else self._placeholder)
            else:
                out.append(ch)
        return "".join(out)
```

### platform/shell/memory/sql_driver/postgres_driver/__init__.py
```
```

### platform/shell/memory/sql_driver/postgres_driver/postgres_driver.py
```
"""postgres_driver.py
PostgresDriver — PostgreSQL stub implementation of SqlDriver.

Wymaga psycopg / psycopg2 (nie zainstalowane domyślnie). Stub do podpięcia
gdy projekt zdecyduje się na Postgres.

Slots:
    _dsn        — connection string ('postgresql://user:pass@host:port/db')
    _connection — Optional; psycopg connection (None until connect)
    _dialect    — Dialect describing Postgres SQL specifics
"""

from __future__ import annotations

from typing import Any, Sequence

from shell.memory.sql_driver.sql_driver import SqlDriver
from shell.memory.sql_driver.dialect import Dialect


_POSTGRES_DIALECT = Dialect(
    placeholder="%s",
    auto_pk="BIGSERIAL PRIMARY KEY",
    blob_type="BYTEA",
    supports_fts=False,
)


class PostgresDriver(SqlDriver):
    """PostgreSQL SqlDriver (stub)."""

    __slots__ = ("_dsn", "_connection", "_dialect")

    def __init__(self, dsn: str) -> None:
        self._dsn: str = dsn
        self._connection = None
        self._dialect: Dialect = _POSTGRES_DIALECT

    @property
    def dialect_(self) -> Dialect:
        return self._dialect

    @property
    def dsn_(self) -> str:
        return self._dsn

    def connect(self) -> None:
        raise NotImplementedError("[PostgresDriver] psycopg integration not implemented yet")

    def close(self) -> None:
        raise NotImplementedError("[PostgresDriver] psycopg integration not implemented yet")

    def execute(self, sql: str, params: Sequence[Any] = ()) -> None:
        raise NotImplementedError("[PostgresDriver] psycopg integration not implemented yet")

    def executemany(self, sql: str, rows: Sequence[Sequence[Any]]) -> None:
        raise NotImplementedError("[PostgresDriver] psycopg integration not implemented yet")

    def executescript(self, script: str) -> None:
        raise NotImplementedError("[PostgresDriver] psycopg integration not implemented yet")

    def query(self, sql: str, params: Sequence[Any] = ()) -> list[dict]:
        raise NotImplementedError("[PostgresDriver] psycopg integration not implemented yet")

    def last_insert_id(self) -> int:
        raise NotImplementedError("[PostgresDriver] psycopg integration not implemented yet")

    def commit(self) -> None:
        raise NotImplementedError("[PostgresDriver] psycopg integration not implemented yet")
```

### platform/shell/memory/sql_driver/sql_driver.py
```
"""sql_driver.py
SqlDriver — abstract bridge between SqlMemoryBackend and a concrete SQL engine.

Slots:
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Sequence

from shell.memory.sql_driver.dialect import Dialect


class SqlDriver(ABC):
    """Abstract SQL driver used by SqlMemoryBackend.

    Implementations: SqliteDriver (default), PostgresDriver, future engines.
    """

    __slots__ = ()

    @property
    @abstractmethod
    def dialect_(self) -> Dialect:
        ...

    @abstractmethod
    def connect(self) -> None:
        ...

    @abstractmethod
    def close(self) -> None:
        ...

    @abstractmethod
    def execute(self, sql: str, params: Sequence[Any] = ()) -> None:
        ...

    @abstractmethod
    def executemany(self, sql: str, rows: Sequence[Sequence[Any]]) -> None:
        ...

    @abstractmethod
    def executescript(self, script: str) -> None:
        ...

    @abstractmethod
    def query(self, sql: str, params: Sequence[Any] = ()) -> list[dict]:
        ...

    @abstractmethod
    def last_insert_id(self) -> int:
        ...

    @abstractmethod
    def commit(self) -> None:
        ...
```

### platform/shell/memory/sql_driver/sqlite_driver/__init__.py
```
```

### platform/shell/memory/sql_driver/sqlite_driver/sqlite_driver.py
```
"""sqlite_driver.py
SqliteDriver — SQLite implementation of SqlDriver (sqlite3, stdlib).

Slots:
    _db_path    — filesystem path to the SQLite database file
    _connection — Optional; sqlite3.Connection (None until connect)
    _dialect    — Dialect describing SQLite SQL specifics
"""

from __future__ import annotations

import sqlite3
from typing import Any, Sequence

from shell.utils.path.path import Path, PathType
from shell.memory.sql_driver.sql_driver import SqlDriver
from shell.memory.sql_driver.dialect import Dialect


_SQLITE_DIALECT = Dialect(
    placeholder="?",
    auto_pk="INTEGER PRIMARY KEY AUTOINCREMENT",
    blob_type="BLOB",
    supports_fts=True,
)


class SqliteDriver(SqlDriver):
    """SQLite SqlDriver."""

    __slots__ = ("_db_path", "_connection", "_dialect")

    def __init__(self, db_path: PathType) -> None:
        self._db_path: PathType = db_path
        self._connection: sqlite3.Connection | None = None
        self._dialect: Dialect = _SQLITE_DIALECT

    @property
    def dialect_(self) -> Dialect:
        return self._dialect

    @property
    def db_path_(self) -> PathType:
        return self._db_path

    @property
    def connection_(self) -> sqlite3.Connection:
        return self._connection

    def connect(self) -> None:
        parent = self._db_path.parent
        if not Path.exists(parent):
            Path.mkdir(parent)
        self._connection = sqlite3.connect(str(self._db_path))
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def execute(self, sql: str, params: Sequence[Any] = ()) -> None:
        self._connection.execute(self._dialect.render_sql(sql), tuple(params))

    def executemany(self, sql: str, rows: Sequence[Sequence[Any]]) -> None:
        self._connection.executemany(self._dialect.render_sql(sql), [tuple(r) for r in rows])

    def executescript(self, script: str) -> None:
        self._connection.executescript(script)

    def query(self, sql: str, params: Sequence[Any] = ()) -> list[dict]:
        cursor = self._connection.execute(self._dialect.render_sql(sql), tuple(params))
        return [dict(row) for row in cursor.fetchall()]

    def last_insert_id(self) -> int:
        row = self._connection.execute("SELECT last_insert_rowid() AS id").fetchone()
        return int(row["id"]) if row else 0

    def commit(self) -> None:
        self._connection.commit()
```

### platform/shell/memory/sql_memory_backend/__init__.py
```
```

### platform/shell/memory/sql_memory_backend/internal/__init__.py
```
```

### platform/shell/memory/sql_memory_backend/internal/_append_message.py
```
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _append_message(
    backend: SqlMemoryBackend,
    correlation_id: str,
    sender: str,
    receiver: str,
    payload: dict,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    backend.driver_.execute(
        """
        INSERT INTO message (correlation_id, sender, receiver, payload_json, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (correlation_id, sender, receiver, json.dumps(payload, ensure_ascii=False), now),
    )
    backend.driver_.commit()
```

### platform/shell/memory/sql_memory_backend/internal/_apply_schema.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _apply_schema(backend: SqlMemoryBackend) -> None:
    dialect = backend.driver_.dialect_
    auto_pk = dialect.auto_pk_
    blob = dialect.blob_type_

    ddl = f"""
    CREATE TABLE IF NOT EXISTS context_entry (
        id              {auto_pk},
        context_type    TEXT NOT NULL,
        scope_id        TEXT NOT NULL,
        entry_key       TEXT NOT NULL,
        value_json      TEXT NOT NULL,
        tags            TEXT,
        created_at      TEXT NOT NULL,
        updated_at      TEXT NOT NULL,
        UNIQUE(context_type, scope_id, entry_key)
    );
    CREATE INDEX IF NOT EXISTS idx_ctx_type_scope ON context_entry(context_type, scope_id);
    CREATE INDEX IF NOT EXISTS idx_ctx_tags       ON context_entry(tags);

    CREATE TABLE IF NOT EXISTS session (
        session_id   TEXT PRIMARY KEY,
        agent_id     TEXT NOT NULL,
        goal         TEXT,
        status       TEXT NOT NULL,
        started_at   TEXT NOT NULL,
        ended_at     TEXT
    );

    CREATE TABLE IF NOT EXISTS message (
        id              {auto_pk},
        correlation_id  TEXT NOT NULL,
        sender          TEXT NOT NULL,
        receiver        TEXT NOT NULL,
        payload_json    TEXT NOT NULL,
        created_at      TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_msg_corr ON message(correlation_id);

    CREATE TABLE IF NOT EXISTS audit_event (
        id           {auto_pk},
        request_id   TEXT NOT NULL,
        trace_id     TEXT,
        "user"       TEXT,
        event_type   TEXT NOT NULL,
        payload_json TEXT,
        timestamp    TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_audit_req ON audit_event(request_id);

    CREATE TABLE IF NOT EXISTS rag_document (
        id          {auto_pk},
        source_uri  TEXT NOT NULL,
        title       TEXT,
        domain      TEXT,
        created_at  TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS rag_chunk (
        id              {auto_pk},
        document_id     INTEGER NOT NULL REFERENCES rag_document(id) ON DELETE CASCADE,
        chunk_index     INTEGER NOT NULL,
        chunk_text      TEXT NOT NULL,
        embedding       {blob},
        embedding_model TEXT,
        UNIQUE(document_id, chunk_index)
    );
    CREATE INDEX IF NOT EXISTS idx_chunk_doc ON rag_chunk(document_id);
    """
    backend.driver_.executescript(ddl)
    if dialect.supports_fts_:
        backend.driver_.executescript(
            "CREATE VIRTUAL TABLE IF NOT EXISTS rag_chunk_fts "
            "USING fts5(chunk_text, content='rag_chunk', content_rowid='id');"
        )
    backend.driver_.commit()
```

### platform/shell/memory/sql_memory_backend/internal/_close_session.py
```
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _close_session(backend: SqlMemoryBackend, session_id: str, status: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    backend.driver_.execute(
        "UPDATE session SET status = ?, ended_at = ? WHERE session_id = ?",
        (status, now, session_id),
    )
    backend.driver_.commit()
```

### platform/shell/memory/sql_memory_backend/internal/_close_sql_memory_backend.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _close_sql_memory_backend(backend: SqlMemoryBackend) -> None:
    backend.driver_.close()
```

### platform/shell/memory/sql_memory_backend/internal/_delete_entry.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _delete_entry(backend: SqlMemoryBackend, context_type: str, scope_id: str, entry_key: str) -> None:
    backend.driver_.execute(
        "DELETE FROM context_entry WHERE context_type = ? AND scope_id = ? AND entry_key = ?",
        (context_type, scope_id, entry_key),
    )
    backend.driver_.commit()
```

### platform/shell/memory/sql_memory_backend/internal/_get_conversation.py
```
from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _get_conversation(backend: SqlMemoryBackend, correlation_id: str) -> list[dict]:
    rows = backend.driver_.query(
        """
        SELECT id, sender, receiver, payload_json, created_at
        FROM message
        WHERE correlation_id = ?
        ORDER BY id
        """,
        (correlation_id,),
    )
    return [
        {
            "id": r["id"],
            "sender": r["sender"],
            "receiver": r["receiver"],
            "payload": json.loads(r["payload_json"]),
            "created_at": r["created_at"],
        }
        for r in rows
    ]
```

### platform/shell/memory/sql_memory_backend/internal/_get_entry.py
```
from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _get_entry(
    backend: SqlMemoryBackend,
    context_type: str,
    scope_id: str,
    entry_key: str,
) -> dict | None:
    rows = backend.driver_.query(
        """
        SELECT value_json, tags, created_at, updated_at
        FROM context_entry
        WHERE context_type = ? AND scope_id = ? AND entry_key = ?
        """,
        (context_type, scope_id, entry_key),
    )
    if not rows:
        return None
    row = rows[0]
    return {
        "value": json.loads(row["value_json"]),
        "tags": row["tags"].split(",") if row["tags"] else [],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
```

### platform/shell/memory/sql_memory_backend/internal/_index_document.py
```
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _index_document(
    backend: SqlMemoryBackend,
    source_uri: str,
    title: str,
    domain: str,
    chunks: list[str],
    embeddings: list[bytes],
    embedding_model: str,
) -> int:
    if len(chunks) != len(embeddings):
        raise ValueError("[SqlMemoryBackend.index_document] chunks and embeddings length mismatch")
    now = datetime.now(timezone.utc).isoformat()
    backend.driver_.execute(
        "INSERT INTO rag_document (source_uri, title, domain, created_at) VALUES (?, ?, ?, ?)",
        (source_uri, title, domain, now),
    )
    document_id = backend.driver_.last_insert_id()
    backend.driver_.executemany(
        """
        INSERT INTO rag_chunk (document_id, chunk_index, chunk_text, embedding, embedding_model)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (document_id, idx, chunk, emb, embedding_model)
            for idx, (chunk, emb) in enumerate(zip(chunks, embeddings))
        ],
    )
    if backend.driver_.dialect_.supports_fts_:
        backend.driver_.executemany(
            "INSERT INTO rag_chunk_fts(rowid, chunk_text) "
            "SELECT id, chunk_text FROM rag_chunk WHERE document_id = ? AND chunk_index = ?",
            [(document_id, idx) for idx in range(len(chunks))],
        )
    backend.driver_.commit()
    return document_id
```

### platform/shell/memory/sql_memory_backend/internal/_init_sql_memory_backend.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

from shell.memory.sql_memory_backend.internal._apply_schema import _apply_schema

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _init_sql_memory_backend(backend: SqlMemoryBackend) -> None:
    backend.driver_.connect()
    _apply_schema(backend)
```

### platform/shell/memory/sql_memory_backend/internal/_list_entries.py
```
from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _list_entries(backend: SqlMemoryBackend, context_type: str, scope_id: str) -> list[dict]:
    rows = backend.driver_.query(
        """
        SELECT entry_key, value_json, tags, created_at, updated_at
        FROM context_entry
        WHERE context_type = ? AND scope_id = ?
        ORDER BY entry_key
        """,
        (context_type, scope_id),
    )
    return [
        {
            "entry_key": r["entry_key"],
            "value": json.loads(r["value_json"]),
            "tags": r["tags"].split(",") if r["tags"] else [],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }
        for r in rows
    ]
```

### platform/shell/memory/sql_memory_backend/internal/_log_event.py
```
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _log_event(
    backend: SqlMemoryBackend,
    request_id: str,
    event_type: str,
    payload: dict,
    trace_id: str | None,
    user: str | None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    backend.driver_.execute(
        """
        INSERT INTO audit_event (request_id, trace_id, "user", event_type, payload_json, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (request_id, trace_id, user, event_type, json.dumps(payload, ensure_ascii=False) if payload else None, now),
    )
    backend.driver_.commit()
```

### platform/shell/memory/sql_memory_backend/internal/_open_session.py
```
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _open_session(backend: SqlMemoryBackend, session_id: str, agent_id: str, goal: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    backend.driver_.execute(
        """
        INSERT INTO session (session_id, agent_id, goal, status, started_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET
            agent_id = excluded.agent_id,
            goal     = excluded.goal,
            status   = excluded.status,
            started_at = excluded.started_at
        """,
        (session_id, agent_id, goal, "active", now),
    )
    backend.driver_.commit()
```

### platform/shell/memory/sql_memory_backend/internal/_put_entry.py
```
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _put_entry(
    backend: SqlMemoryBackend,
    context_type: str,
    scope_id: str,
    entry_key: str,
    value: dict,
    tags: list[str] | None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    tags_csv = ",".join(tags) if tags else None
    value_json = json.dumps(value, ensure_ascii=False)
    backend.driver_.execute(
        """
        INSERT INTO context_entry (context_type, scope_id, entry_key, value_json, tags, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(context_type, scope_id, entry_key) DO UPDATE SET
            value_json = excluded.value_json,
            tags       = excluded.tags,
            updated_at = excluded.updated_at
        """,
        (context_type, scope_id, entry_key, value_json, tags_csv, now, now),
    )
    backend.driver_.commit()
```

### platform/shell/memory/sql_memory_backend/internal/_search_fts.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _search_fts(backend: SqlMemoryBackend, query_text: str, top_k: int) -> list[dict]:
    if not backend.driver_.dialect_.supports_fts_:
        return []
    rows = backend.driver_.query(
        """
        SELECT c.id, c.document_id, c.chunk_index, c.chunk_text,
               d.source_uri, d.title, d.domain,
               bm25(rag_chunk_fts) AS score
        FROM rag_chunk_fts
        JOIN rag_chunk c ON c.id = rag_chunk_fts.rowid
        JOIN rag_document d ON d.id = c.document_id
        WHERE rag_chunk_fts MATCH ?
        ORDER BY score
        LIMIT ?
        """,
        (query_text, top_k),
    )
    return [
        {
            "score": r["score"],
            "chunk_id": r["id"],
            "document_id": r["document_id"],
            "chunk_index": r["chunk_index"],
            "chunk_text": r["chunk_text"],
            "source_uri": r["source_uri"],
            "title": r["title"],
            "domain": r["domain"],
        }
        for r in rows
    ]
```

### platform/shell/memory/sql_memory_backend/internal/_search_rag.py
```
from __future__ import annotations

import struct
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend


def _decode_vector(blob: bytes) -> list[float]:
    count = len(blob) // 4
    return list(struct.unpack(f"{count}f", blob))


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def _search_rag(
    backend: SqlMemoryBackend,
    query_embedding: bytes,
    top_k: int,
    domain: str | None,
) -> list[dict]:
    query_vec = _decode_vector(query_embedding)
    if domain:
        rows = backend.driver_.query(
            """
            SELECT c.id, c.document_id, c.chunk_index, c.chunk_text, c.embedding,
                   d.source_uri, d.title, d.domain
            FROM rag_chunk c JOIN rag_document d ON d.id = c.document_id
            WHERE d.domain = ? AND c.embedding IS NOT NULL
            """,
            (domain,),
        )
    else:
        rows = backend.driver_.query(
            """
            SELECT c.id, c.document_id, c.chunk_index, c.chunk_text, c.embedding,
                   d.source_uri, d.title, d.domain
            FROM rag_chunk c JOIN rag_document d ON d.id = c.document_id
            WHERE c.embedding IS NOT NULL
            """,
        )
    scored = []
    for r in rows:
        score = _cosine_similarity(query_vec, _decode_vector(r["embedding"]))
        scored.append((score, r))
    scored.sort(key=lambda t: t[0], reverse=True)
    return [
        {
            "score": score,
            "chunk_id": r["id"],
            "document_id": r["document_id"],
            "chunk_index": r["chunk_index"],
            "chunk_text": r["chunk_text"],
            "source_uri": r["source_uri"],
            "title": r["title"],
            "domain": r["domain"],
        }
        for score, r in scored[:top_k]
    ]
```

### platform/shell/memory/sql_memory_backend/sql_memory_backend.py
```
"""sql_memory_backend.py
SqlMemoryBackend — SQL-based MemoryBackend that uses any SqlDriver (bridge).

Wymiana bazy = wstrzyknięcie innego drivera w konstruktorze.

Slots:
    _driver — SqlDriver instance (sqlite/postgres/...)
"""

from __future__ import annotations

from shell.memory.memory_backend.memory_backend import MemoryBackend
from shell.memory.sql_driver.sql_driver import SqlDriver
from shell.memory.sql_memory_backend.internal._init_sql_memory_backend import _init_sql_memory_backend
from shell.memory.sql_memory_backend.internal._close_sql_memory_backend import _close_sql_memory_backend
from shell.memory.sql_memory_backend.internal._put_entry import _put_entry
from shell.memory.sql_memory_backend.internal._get_entry import _get_entry
from shell.memory.sql_memory_backend.internal._list_entries import _list_entries
from shell.memory.sql_memory_backend.internal._delete_entry import _delete_entry
from shell.memory.sql_memory_backend.internal._open_session import _open_session
from shell.memory.sql_memory_backend.internal._close_session import _close_session
from shell.memory.sql_memory_backend.internal._append_message import _append_message
from shell.memory.sql_memory_backend.internal._get_conversation import _get_conversation
from shell.memory.sql_memory_backend.internal._log_event import _log_event
from shell.memory.sql_memory_backend.internal._index_document import _index_document
from shell.memory.sql_memory_backend.internal._search_rag import _search_rag
from shell.memory.sql_memory_backend.internal._search_fts import _search_fts


class SqlMemoryBackend(MemoryBackend):
    """SQL-based MemoryBackend powered by a pluggable SqlDriver."""

    __slots__ = ("_driver",)

    def __init__(self, driver: SqlDriver) -> None:
        self._driver: SqlDriver = driver

    @property
    def driver_(self) -> SqlDriver:
        return self._driver

    def init_backend(self) -> None:
        _init_sql_memory_backend(self)

    def close_backend(self) -> None:
        _close_sql_memory_backend(self)

    def put_entry(self, context_type, scope_id, entry_key, value, tags=None):
        _put_entry(self, context_type, scope_id, entry_key, value, tags)

    def get_entry(self, context_type, scope_id, entry_key):
        return _get_entry(self, context_type, scope_id, entry_key)

    def list_entries(self, context_type, scope_id):
        return _list_entries(self, context_type, scope_id)

    def delete_entry(self, context_type, scope_id, entry_key):
        _delete_entry(self, context_type, scope_id, entry_key)

    def open_session(self, session_id, agent_id, goal):
        _open_session(self, session_id, agent_id, goal)

    def close_session(self, session_id, status):
        _close_session(self, session_id, status)

    def append_message(self, correlation_id, sender, receiver, payload):
        _append_message(self, correlation_id, sender, receiver, payload)

    def get_conversation(self, correlation_id):
        return _get_conversation(self, correlation_id)

    def log_event(self, request_id, event_type, payload, trace_id=None, user=None):
        _log_event(self, request_id, event_type, payload, trace_id, user)

    def index_document(self, source_uri, title, domain, chunks, embeddings, embedding_model):
        return _index_document(self, source_uri, title, domain, chunks, embeddings, embedding_model)

    def search_rag(self, query_embedding, top_k=5, domain=None):
        return _search_rag(self, query_embedding, top_k, domain)

    def search_fts(self, query_text, top_k=5):
        return _search_fts(self, query_text, top_k)
```

### platform/shell/module/__init__.py
```
```

### platform/shell/module/agent/__init__.py
```
from shell.module.agent.agent.agent import Agent
```

### platform/shell/module/agent/agent/__init__.py
```
from shell.module.agent.agent.agent import Agent

__all__ = ["Agent"]
```

### platform/shell/module/agent/agent/agent.py
```
"""Entry point for Agent command construction and execution."""

from __future__ import annotations

from collections.abc import Callable
from subprocess import CompletedProcess

from shell.module.agent.agent.internal._init_agent import _init_agent
from shell.module.agent.agent.internal._run_agent import _run_agent
from shell.module.agent.agent_prompt.agent_prompt import AgentPrompt
from shell.module.agent.agent_properties.agent_properties import AgentProperties


class Agent:
    """
    Slots:
        _app              — parent App
        _which            — Optional; injectable shutil.which replacement
        _os_name          — Optional; injectable os.name replacement
        _agent_prompt     — AgentPrompt
        _agent_properties — AgentProperties
    """

    __slots__ = ("_app", "_which", "_os_name", "_agent_prompt", "_agent_properties")

    def __init__(self, app, which=None, os_name=None) -> None:
        self._app = app
        self._which = which
        self._os_name = os_name
        self._agent_prompt: AgentPrompt | None = None
        self._agent_properties: AgentProperties | None = None

    @property
    def which_(self):
        return self._which

    @property
    def os_name_(self):
        return self._os_name

    @property
    def agent_prompt_(self) -> AgentPrompt:
        if self._agent_prompt is None:
            self._agent_prompt = AgentPrompt(self._app)
        return self._agent_prompt

    @property
    def agent_properties_(self) -> AgentProperties:
        if self._agent_properties is None:
            self._agent_properties = AgentProperties(self._app)
        return self._agent_properties

    def init_agent(self) -> None:
        _init_agent(self)

    def run_agent(
        self,
        runner: Callable[..., CompletedProcess] | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        _run_agent(self, runner=runner, sleep=sleep)
```

### platform/shell/module/agent/agent/internal/__init__.py
```
```

### platform/shell/module/agent/agent/internal/_assert_prompt_not_empty.py
```
"""_assert_prompt_not_empty.py
Responsible for one thing: raising ValueError when prompt is empty.
"""


def _assert_prompt_not_empty(prompt: str) -> None:
    """Raise ValueError if prompt is falsy."""
    if not prompt:
        raise ValueError("[_run_agent] prompt is required and cannot be empty")
```

### platform/shell/module/agent/agent/internal/_init_agent.py
```
from __future__ import annotations


def _init_agent(agent) -> None:
    agent.agent_properties_.init_agent_properties()
    agent.agent_prompt_.init_agent_prompt()
```

### platform/shell/module/agent/agent/internal/_run_agent.py
```
"""run_agent.py
Responsible for one thing: running the CLI command via subprocess,
capturing stdout/stderr, handling TimeoutExpired and retries.
Writes stdout, stderr, returncode to app.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from subprocess import CompletedProcess

from shell.module.agent.agent.internal._run_once import _run_once
from shell.module.agent.agent.internal._assert_prompt_not_empty import _assert_prompt_not_empty
from shell.status.status import Status


def _run_agent(
    agent,
    runner: Callable[..., CompletedProcess] | None = None,
    sleep: Callable[[float], None] | None = None,
) -> Status:
    """Run the CLI command with optional retries.

    Prompt is passed via stdin.
    Writes stdout, stderr, returncode to app.
    After all attempts failed: escalates to error and raises.
    runner: optional callable replacing subprocess.run (for testing).
    sleep: optional callable replacing time.sleep (for testing).
    """
    if sleep is None:
        sleep = time.sleep
    app = agent._app
    which = agent.which_
    os_name = agent.os_name_
    timeout: int = app.runner_.agent_.agent_properties_.timeout_
    retries: int = app.runner_.agent_.agent_properties_.retries_
    retry_delay: float = app.runner_.agent_.agent_properties_.retry_delay_
    prompt: str = app.runner_.agent_.agent_prompt_.prompt()

    prompt = app.placeholders_.apply(prompt)
    _assert_prompt_not_empty(prompt)
    app.app_trace_.record_info('agent._run_agent._run_agent', f'cwd: {app.app_node_.node_.node_dir_}')
    app.app_trace_.record_info('agent._run_agent._run_agent', f'timeout={timeout} retries={retries} retry_delay={retry_delay}')
    app.app_trace_.record_info('agent._run_agent._run_agent', f'prompt ({len(prompt)} chars):\n{prompt}')

    for attempt in range(retries + 1):

        status = _run_once(prompt=prompt, timeout=timeout, app=app, runner=runner, which=which, os_name=os_name)

        if status == Status.SUCCESS:
            app.app_trace_.record_info('agent._run_agent._run_agent', f'Command succeeded on attempt {attempt + 1}.')
            return status

        if attempt < retries:
            app.app_trace_.record_info('agent._run_agent._run_agent', f"Retry {attempt + 1}/{retries} after {retry_delay:.1f}s...")
            sleep(retry_delay)

    app.app_trace_.record_error_and_raise('agent._run_agent._run_agent', RuntimeError(f'Command failed after {retries + 1} attempt(s).'))
```

### platform/shell/module/agent/agent/internal/_run_once.py
```
from __future__ import annotations

import subprocess

from shell.component.process.process.process import Process
from shell.status.status import Status


def _run_once(
    prompt: str,
    timeout: int,
    app,
    runner=None,
    which=None,
    os_name=None,
) -> Status:
    process = Process(app, runner)
    process.init_process_agent(prompt, timeout, which, os_name)
    try:
        process.run_process()
        app.app_trace_.record_info('agent._run_once._run_once', f'returncode={process.returncode_}', stdout=process.stdout_, stderr=process.stderr_, returncode=process.returncode_)
        if process.stdout_ and process.stdout_.strip():
            app.app_trace_.record_info('agent._run_once._run_once', f'stdout:\n{process.stdout_.strip()}', stdout=process.stdout_, returncode=process.returncode_)
        if process.stderr_:
            if process.returncode_ == 0:
                app.app_trace_.record_info('agent._run_once._run_once', f"stderr (returncode={process.returncode_}): {process.stderr_.strip()}", stdout=process.stdout_, stderr=process.stderr_, returncode=process.returncode_)
            else:
                app.app_trace_.record_warning('agent._run_once._run_once', Exception(f"stderr (returncode={process.returncode_}): {process.stderr_.strip()}"), stdout=process.stdout_, stderr=process.stderr_, returncode=process.returncode_)
        return Status.from_returncode(process.returncode_)
    except subprocess.TimeoutExpired as exc:
        partial_out = exc.output or ""
        partial_err = exc.stderr or f"Timeout after {timeout}s"
        app.app_trace_.record_warning_and_raise('agent._run_once._run_once', exc, stdout=partial_out, stderr=partial_err)
    except OSError as exc:
        app.app_trace_.record_error_and_raise('agent._run_once._run_once', exc)
    except Exception as exc:  # noqa: BLE001
        app.app_trace_.record_warning_and_raise('agent._run_once._run_once', exc)
```

### platform/shell/module/agent/agent_prompt/__init__.py
```
# lib/prompt package
```

### platform/shell/module/agent/agent_prompt/agent_prompt.py
```
"""agent_prompt.py
AgentPrompt: single entry point for prompt state for a single node run.

Fields (own):
    _app            — parent App (DOM back-reference)
    _prompt_cli     — CLI prompt (PromptCli | None)
    _prompt_role    — role prompts loaded from task-dir (PromptRole | None)
    _prompt_skill   — skill prompts loaded from source-dir (PromptSkill | None)
    _prompt_system  — system prompts loaded from task-dir (PromptSystem | None)

Properties:
    prompt_cli_     — lazy PromptCli instance
    prompt_role_    — lazy PromptRole instance
    prompt_skill_   — lazy PromptSkill instance
    prompt_system_  — lazy PromptSystem instance
"""

from __future__ import annotations

from shell.module.agent.agent_prompt.internal._init_agent_prompt import _init_agent_prompt
from shell.module.agent.agent_prompt.internal._build_prompt_from_input import _build_prompt_from_input
from shell.component.prompt.prompt_cli.prompt_cli import PromptCli
from shell.component.prompt.prompt_role.prompt_role import PromptRole
from shell.component.prompt.prompt_skill.prompt_skill import PromptSkill
from shell.component.prompt.prompt_system.prompt_system import PromptSystem


class AgentPrompt:
    """Manages prompt state for a single node run.

    Constructed as AgentPrompt(app). Call init_agent_prompt() to populate from app.
    """

    __slots__ = ("_app", "_prompt_cli", "_prompt_role", "_prompt_skill", "_prompt_system")

    def __init__(self, app=None) -> None:
        self._app = app
        self._prompt_cli: PromptCli | None = None
        self._prompt_role: PromptRole | None = None
        self._prompt_skill: PromptSkill | None = None
        self._prompt_system: PromptSystem | None = None

    @property
    def prompt_cli_(self) -> PromptCli:
        if self._prompt_cli is None:
            self._prompt_cli = PromptCli()
        return self._prompt_cli

    @property
    def prompt_role_(self) -> PromptRole:
        if self._prompt_role is None:
            self._prompt_role = PromptRole()
        return self._prompt_role

    @property
    def prompt_skill_(self) -> PromptSkill:
        if self._prompt_skill is None:
            self._prompt_skill = PromptSkill()
        return self._prompt_skill

    @property
    def prompt_system_(self) -> PromptSystem:
        if self._prompt_system is None:
            self._prompt_system = PromptSystem()
        return self._prompt_system

    # -----------------------------------------------------------------------
    # DOM operation
    # -----------------------------------------------------------------------

    def init_agent_prompt(self) -> None:
        _init_agent_prompt(self)

    def prompt(self) -> str:
        cli_body = self._prompt_cli.prompt_file_.file_body_ if self._prompt_cli is not None else None
        if cli_body:
            return cli_body
        parts = [self._prompt_role.prompt(), self._prompt_skill.prompt(), self._prompt_system.prompt()]
        base = "\n\n".join(p for p in parts if p)
        input_section = _build_prompt_from_input(self._app)
        if input_section:
            return base + "\n\n" + input_section if base else input_section
        return base
```

### platform/shell/module/agent/agent_prompt/internal/__init__.py
```
```

### platform/shell/module/agent/agent_prompt/internal/_assert_role_resolved.py
```
def _assert_role_resolved(role) -> None:
    if role is None:
        raise ValueError("role is not set — required for prompt_role loading")
```

### platform/shell/module/agent/agent_prompt/internal/_assert_role_set.py
```
def _assert_role_set(role) -> None:
    if not role:
        raise ValueError("[init_system_prompt] 'role' is required in app but was not set.")
```

### platform/shell/module/agent/agent_prompt/internal/_assert_task_dir_resolved.py
```
def _assert_task_dir_resolved(task_dir) -> None:
    if task_dir is None:
        raise ValueError("task_dir is not set — required for prompt_role loading")
```

### platform/shell/module/agent/agent_prompt/internal/_build_from_dir.py
```
from __future__ import annotations


from shell.utils.io.io import default_read_utf8_safe
from shell.module.agent.agent_prompt.internal._clean_name import _clean_name
from shell.utils.path.path import Path, PathType

_TEXT_SUFFIXES = {".md", ".txt", ".yaml", ".yml", ".json"}


def _build_from_dir(directory: PathType, reader=None) -> str:
    if reader is None:
        reader = default_read_utf8_safe
    files = sorted(
        (f for f in Path.iterdir(directory) if Path.is_file(f) and f.suffix in _TEXT_SUFFIXES),
        key=lambda f: f.name,
    )

    if not files:
        return ""

    sections: list[str] = []

    for idx, file in enumerate(files, 1):
        sections.append(f"# {idx}. {_clean_name(file.stem)}")
        try:
            sections.append(reader(file))
        except OSError:
            sections.append("<unreadable>")

    return "\n\n".join(sections)
```

### platform/shell/module/agent/agent_prompt/internal/_build_prompt_from_input.py
```
"""_build_prompt_from_input.py
Private. Responsible for one thing: building the full prompt string from
*.md files already loaded into app.app_node_.node_.node_input_.input_files_map_.
"""

from __future__ import annotations

from shell.utils.path.path import Path, PathType

from shell.module.agent.agent_prompt.internal._clean_name import _clean_name


def _build_prompt_from_input(app, reader=None) -> str:
    input_files_map = app.app_node_.node_.node_input_.input_files_map_
    if not input_files_map:
        return ""

    sections: list[str] = []
    for idx, (file, file_name) in enumerate(input_files_map.items(), 1):
        sections.append(f"# {idx}. {_clean_name(Path.new(file_name).stem)}")
        file_body = file.file_body_
        sections.append(file_body if file_body else "<unreadable>")

    return "\n\n".join(sections)
```

### platform/shell/module/agent/agent_prompt/internal/_clean_name.py
```
"""_clean_name.py
Private. Responsible for one thing: turning a NNNN_snake_case stem into a
human-readable section heading (e.g. '0010_task_instructions' -> 'Task instructions').
"""

import re

_NUMERIC_PREFIX = re.compile(r"^\d+_")


def _clean_name(stem: str) -> str:
    """Strip leading digits+underscore, replace underscores with spaces, capitalize."""
    return _NUMERIC_PREFIX.sub("", stem).replace("_", " ").capitalize()
```

### platform/shell/module/agent/agent_prompt/internal/_create_prompt.py
```
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
```

### platform/shell/module/agent/agent_prompt/internal/_find_file.py
```

from shell.utils.path.path import Path, PathType


def _find_file(filename: str, node: PathType) -> PathType | None:
    for search_dir in [node / ".node" / "input", node / ".node" / "temp"]:
        if not Path.is_dir(search_dir):
            continue
        for match in Path.rglob(search_dir, filename):
            if Path.is_file(match):
                return match
    return None
```

### platform/shell/module/agent/agent_prompt/internal/_has_system_prompt.py
```
"""_has_system_prompt.py
Private. Responsible for one thing: checking whether a system prompt file
for the given role already exists in the input/ directory.
"""

import re

from shell.utils.path.path import Path, PathType


def _has_system_prompt(input_dir: PathType, role: str) -> bool:
    if not Path.is_dir(input_dir):
        return False
    pattern = re.compile(rf'^\d{{4}}_system_{re.escape(role)}\.md$')
    return any(pattern.match(f.name) for f in Path.iterdir(input_dir) if Path.is_file(f))
```
