### platform/dirnode/component/runner/runner/runner.py
```
"""runner.py
Runner — domain methods shared by all runner types.

Owns _app, _agent, _mode and _runner_properties slots.

Domain methods (per spec):
    run_runner(timer)    — dispatch CLI flags to the appropriate domain method
"""

from __future__ import annotations

from dirnode.module.agent.agent.agent import Agent
from dirnode.module.router.router.router import Router
from dirnode.component.runner.runner.internal._init_runner import _init_runner
from dirnode.component.runner.runner.internal._run_runner import _run_runner
from dirnode.component.runner.runner_properties.runner_properties import RunnerProperties
from dirnode.module.tasker.tasker import Tasker
from dirnode.module.tool.tool import Tool
from dirnode.module.worker.worker.worker import Worker

_MODES: frozenset[str] = frozenset({"agent", "tasker", "router", "tool", "worker"})


class Runner:
    """Domain methods for a single node run.

    Cached via app.runner_.
    """

    __slots__ = ("_app", "_agent", "_mode", "_runner_properties", "_tasker", "_router", "_tool", "_worker")

    def __init__(self, app=None) -> None:
        self._app = app
        self._agent: Agent | None = None
        self._mode: str | None = None
        self._runner_properties: RunnerProperties | None = None
        self._tasker: Tasker | None = None
        self._router: Router | None = None
        self._tool: Tool | None = None
        self._worker: Worker | None = None
    # -----------------------------------------------------------------------
    # Slot properties
    # -----------------------------------------------------------------------

    @property
    def agent_(self) -> Agent:
        """Return the cached Agent instance for this runner."""
        if self._agent is None:
            self._agent = Agent(self._app)
        return self._agent

    @property
    def runner_properties_(self) -> RunnerProperties:
        """Return the RunnerProperties instance for this runner."""
        if self._runner_properties is None:
            self._runner_properties = RunnerProperties()
        return self._runner_properties

    @property
    def tasker_(self) -> Tasker:
        """Return the cached Tasker instance for this runner."""
        if self._tasker is None:
            self._tasker = Tasker(self._app)
        return self._tasker

    @property
    def router_(self) -> Router:
        """Return the cached Router instance for this runner."""
        if self._router is None:
            self._router = Router(self._app)
        return self._router

    @property
    def tool_(self) -> Tool:
        """Return the cached Tool instance for this runner."""
        if self._tool is None:
            self._tool = Tool(self._app)
        return self._tool

    @property
    def worker_(self) -> Worker:
        """Return the cached Worker instance for this runner."""
        if self._worker is None:
            self._worker = Worker(self._app)
        return self._worker

    def __repr__(self) -> str:
        return f"Runner(mode={self._mode!r})"

    @property
    def mode_(self) -> str | None:
        if self._mode is None:
            return None
        if self._mode not in _MODES:
            raise ValueError(f"mode must be one of {sorted(_MODES)!r}, got {self._mode!r}")
        return self._mode

    # -----------------------------------------------------------------------
    # Mode predicates
    # -----------------------------------------------------------------------

    @property
    def is_agent_(self) -> bool:
        return self.mode_ == 'agent'

    @property
    def is_router_(self) -> bool:
        return self.mode_ == 'router'

    @property
    def is_tasker_(self) -> bool:
        return self.mode_ == 'tasker'

    @property
    def is_tool_(self) -> bool:
        return self.mode_ == 'tool'

    @property
    def is_worker_(self) -> bool:
        return self.mode_ == 'worker'

    # -----------------------------------------------------------------------
    # Init
    # -----------------------------------------------------------------------

    def init_runner(self, mode: str | None = None) -> None:
        if mode is not None:
            self._mode = mode
        _init_runner(self)

    # -----------------------------------------------------------------------
    # Dispatch (spec: Runner.run_runner)
    # -----------------------------------------------------------------------

    def run_runner(self, timer=None) -> None:
        """Dispatch CLI flags to the appropriate domain method."""
        _run_runner(self, timer=timer)

```

### platform/dirnode/component/runner/runner_properties/__init__.py
```
```

### platform/dirnode/component/runner/runner_properties/runner_properties.py
```
"""runner_properties.py
RunnerProperties — runtime execution parameters for the runner.

Slots:
    add_dirs — list of extra directories passed via --add-dir CLI flags
"""

from __future__ import annotations


class RunnerProperties:
    """Holds runner-level execution parameters."""

    __slots__ = ("_add_dirs",)

    def __init__(self) -> None:
        self._add_dirs: list[str] | None = None

    @property
    def add_dirs_(self) -> list[str]:
        """Return add_dirs list (empty list when not set)."""
        return self._add_dirs or []
```

### platform/dirnode/component/runtime/__init__.py
```
from dirnode.component.runtime.runtime.runtime import Runtime
```

### platform/dirnode/component/runtime/runtime/__init__.py
```
from dirnode.component.runtime.runtime.runtime import Runtime
```

### platform/dirnode/component/runtime/runtime/internal/_init_runtime.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

from dirnode.utils.system.system import System
from dirnode.component.runtime.runtime.internal._init_manifest import _init_manifest
from dirnode.component.runtime.runtime.internal._init_runtime_config import _init_runtime_config

if TYPE_CHECKING:
    from dirnode.component.runtime.runtime.runtime import Runtime


def _init_runtime(runtime: Runtime, version_info: tuple[int, ...] | None = None) -> None:
    System().validate(version_info=version_info)
    _init_runtime_config(runtime)
    _init_manifest(runtime)
```

### platform/dirnode/component/runtime/runtime/internal/_init_runtime_config.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

from dirnode.constants.constants import CONFIG_DIR, CONFIG_YAML

if TYPE_CHECKING:
    from dirnode.component.runtime.runtime.runtime import Runtime


def _init_runtime_config(runtime: Runtime) -> None:
    config_path = runtime.app_.cli_.cli_properties_.runner_root_dir_ / CONFIG_DIR / CONFIG_YAML
    runtime.runtime_config_.init_config(config_path, source='runtime')
```

### platform/dirnode/component/runtime/runtime/runtime.py
```
"""runtime.py
Runtime — container for runtime-level objects shared across the pipeline run.

Slots:
    _app                — Optional; App instance
    _manifest           — Optional; Manifest instance
    _runtime_config     — Optional; Config instance
    _runtime_properties — Optional; RuntimeProperties instance
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dirnode.component.manifest.manifest import Manifest
from dirnode.component.config.config.config import Config
from dirnode.component.runtime.runtime_properties.runtime_properties import RuntimeProperties
from dirnode.component.runtime.runtime.internal._init_runtime import _init_runtime

if TYPE_CHECKING:
    from dirnode.app.app.app import App


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

### platform/dirnode/component/runtime/runtime.md
```
Modul glowny runtime

Grupuje klasy odpowiedzialne za informacje dotyczace aktualnie uruchomionemu runtimowi
to co jest w katalogu z ktorego runtime jest fizycznie uruchomiony czyli , nazwa pliku wykonywalnego
polozenie pliku wykonywalnego, manifest oraz defoltowy config z podstawowymi parametrami
```

### platform/dirnode/component/runtime/runtime_properties/__init__.py
```
from dirnode.component.runtime.runtime_properties.runtime_properties import RuntimeProperties
```

### platform/dirnode/component/runtime/runtime_properties/internal/__init__.py
```
```

### platform/dirnode/component/runtime/runtime_properties/internal/_assert_runtime_properties_loaded.py
```
def _assert_runtime_properties_loaded(name: str | None) -> None:
    if name is None:
        raise ValueError("[RuntimeProperties] not loaded — call init_runtime() first")
```

### platform/dirnode/component/runtime/runtime_properties/runtime_properties.py
```
"""runtime_properties.py
RuntimeProperties — typed accessors for runtime's config.yaml values.

Slots:
    _runtime — parent Runtime
"""

from __future__ import annotations

from dirnode.component.runtime.runtime_properties.internal._assert_runtime_properties_loaded import _assert_runtime_properties_loaded


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

### platform/dirnode/constants/__init__.py
```
```

### platform/dirnode/constants/constants.py
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

### platform/dirnode/dirmode.md
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

### platform/dirnode/docs/opis_platformy.md
```
```

### platform/dirnode/logger/__init__.py
```
# lib/logger package
from dirnode.logger.logger import Logger

__all__ = ["Logger"]
```

### platform/dirnode/logger/internal/__init__.py
```
```

### platform/dirnode/logger/internal/_build_log_path.py
```
from dirnode.utils.path.path import PathType
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

### platform/dirnode/logger/internal/_get_logger.py
```
from dirnode.utils.path.path import PathType
"""_get_logger.py
Private. Responsible for one thing: providing a configured logger
that writes to a log file (configured level) and stderr (WARNING+).

Log format: timestamp | level | message
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from dirnode.utils.io.io import default_file_handler, default_make_dirs
from dirnode.logger.internal._build_log_path import _build_log_path
from dirnode.logger.internal._make_formatter import _make_formatter
from dirnode.logger.internal._resolve_level import _resolve_level


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

### platform/dirnode/logger/internal/_make_formatter.py
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

### platform/dirnode/logger/internal/_resolve_level.py
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

### platform/dirnode/logger/logger.md
```
Modul loggera udostepnia metody loggujace odbiorca jego metod jest modul trace poniewaz on jest akumulatorem loggera
```

### platform/dirnode/logger/logger.py
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

from dirnode.logger.internal._get_logger import _get_logger


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

### platform/dirnode/module/__init__.py
```
```

### platform/dirnode/module/agent/__init__.py
```
from dirnode.module.agent.agent.agent import Agent
```

### platform/dirnode/module/agent/agent/__init__.py
```
from dirnode.module.agent.agent.agent import Agent

__all__ = ["Agent"]
```

### platform/dirnode/module/agent/agent/agent.py
```
"""Entry point for Agent command construction and execution."""

from __future__ import annotations

from collections.abc import Callable
from subprocess import CompletedProcess

from dirnode.module.agent.agent.internal._init_agent import _init_agent
from dirnode.module.agent.agent.internal._run_agent import _run_agent
from dirnode.module.agent.agent_command.agent_command import AgentCommand
from dirnode.module.agent.agent_prompt.agent_prompt import AgentPrompt
from dirnode.module.agent.agent_properties.agent_properties import AgentProperties


class Agent:
    __slots__ = ("_app","_agent_command", "_agent_prompt", "_agent_properties")

    def __init__(self, app, which=None, os_name=None) -> None:
        self._app = app
        self._agent_command: AgentCommand = AgentCommand(app, which, os_name)
        self._agent_prompt: AgentPrompt = AgentPrompt(app)
        self._agent_properties: AgentProperties = AgentProperties(app)

    # -----------------------------------------------------------------------
    # Slot properties
    # -----------------------------------------------------------------------

    @property
    def agent_command_(self) -> AgentCommand:
        return self._agent_command

    @property
    def agent_prompt_(self) -> AgentPrompt:
        return self._agent_prompt

    @property
    def agent_properties_(self) -> AgentProperties:
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

### platform/dirnode/module/agent/agent/internal/__init__.py
```
```

### platform/dirnode/module/agent/agent/internal/_assert_prompt_not_empty.py
```
"""_assert_prompt_not_empty.py
Responsible for one thing: raising ValueError when prompt is empty.
"""


def _assert_prompt_not_empty(prompt: str) -> None:
    """Raise ValueError if prompt is falsy."""
    if not prompt:
        raise ValueError("[_run_agent] prompt is required and cannot be empty")
```

### platform/dirnode/module/agent/agent/internal/_init_agent.py
```
"""_init_agent.py
Initialise Agent sub-objects from _app.
"""

from __future__ import annotations


def _init_agent(agent) -> None:
    """Initialise Agent — each sub-object reads from _app directly."""
    agent._agent_properties.init_agent_properties()
    agent._agent_command.init_agent_command()
    agent._agent_prompt.init_agent_prompt()
```

### platform/dirnode/module/agent/agent/internal/_run_agent.py
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

from dirnode.module.agent.agent.internal._run_once import _run_once
from dirnode.module.agent.agent.internal._assert_prompt_not_empty import _assert_prompt_not_empty
from dirnode.status.status import Status


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
    cmd: list[str] = agent._agent_command.command_
    timeout: int = app.runner_.agent_.agent_properties_.timeout_
    retries: int = app.runner_.agent_.agent_properties_.retries_
    retry_delay: float = app.runner_.agent_.agent_properties_.retry_delay_
    prompt: str = app.runner_.agent_.agent_prompt_.prompt()
    cli = app.cli_
    app.app_trace_.record_info('agent._run_agent._run_agent', f'parent_thread_id={cli.parent_thread_id_} thread_id={cli.thread_id_}')
    binds = [(name, value) for name, value in app.placeholders_.placeholder_list_]
    app.app_trace_.record_info('agent._run_agent._run_agent', f'placeholders before apply: {binds}')
    prompt = app.placeholders_.apply(prompt)
    _assert_prompt_not_empty(prompt)
    app.app_trace_.record_info('agent._run_agent._run_agent', f'cmd: {cmd}')
    app.app_trace_.record_info('agent._run_agent._run_agent', f'cwd: {app.app_node_.node_.node_dir_}')
    app.app_trace_.record_info('agent._run_agent._run_agent', f'timeout={timeout} retries={retries} retry_delay={retry_delay}')
    app.app_trace_.record_info('agent._run_agent._run_agent', f'prompt ({len(prompt)} chars):\n{prompt}')

    for attempt in range(retries + 1):

        status = _run_once(cmd=cmd, prompt=prompt, timeout=timeout, app=app, runner=runner)

        if status == Status.SUCCESS:
            app.app_trace_.record_info('agent._run_agent._run_agent', f'Command succeeded on attempt {attempt + 1}.')
            return status

        if attempt < retries:
            app.app_trace_.record_info('agent._run_agent._run_agent', f"Retry {attempt + 1}/{retries} after {retry_delay:.1f}s...")
            sleep(retry_delay)

    app.app_trace_.record_error_and_raise('agent._run_agent._run_agent', RuntimeError(f'Command failed after {retries + 1} attempt(s).'))
```

### platform/dirnode/module/agent/agent/internal/_run_once.py
```
"""_run_once.py
Responsible for one thing: running a CLI command once via subprocess.
Writes stdout, stderr, returncode to app.
On any error sets warning status.
"""

import subprocess

from dirnode.status.status import Status


def _run_once(
    cmd: list[str],
    prompt: str,
    timeout: int,
    app,
    runner=None,
) -> Status:
    if runner is None:
        runner = subprocess.run
    node_dir = app.app_node_.node_.node_dir_
    try:
        proc = runner(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
            cwd=node_dir,
        )
        app.app_trace_.record_info('agent._run_once._run_once', f'returncode={proc.returncode}', stdout=proc.stdout, stderr=proc.stderr, returncode=proc.returncode)
        if proc.stdout and proc.stdout.strip():
            app.app_trace_.record_info('agent._run_once._run_once', f'stdout:\n{proc.stdout.strip()}', stdout=proc.stdout, returncode=proc.returncode)
        if proc.stderr:
            if proc.returncode == 0:
                app.app_trace_.record_info('agent._run_once._run_once', f"stderr (returncode={proc.returncode}): {proc.stderr.strip()}", stdout=proc.stdout, stderr=proc.stderr, returncode=proc.returncode)
            else:
                app.app_trace_.record_warning('agent._run_once._run_once', Exception(f"stderr (returncode={proc.returncode}): {proc.stderr.strip()}"), stdout=proc.stdout, stderr=proc.stderr, returncode=proc.returncode)
        return Status.from_returncode(proc.returncode)
    except subprocess.TimeoutExpired as exc:
        partial_out = exc.output or ""
        partial_err = exc.stderr or f"Timeout after {timeout}s"
        app.app_trace_.record_warning_and_raise('agent._run_once._run_once', exc, stdout=partial_out, stderr=partial_err)
    except OSError as exc:
        app.app_trace_.record_error_and_raise('agent._run_once._run_once', exc)
    except Exception as exc:  # noqa: BLE001
        app.app_trace_.record_warning_and_raise('agent._run_once._run_once', exc)
```

### platform/dirnode/module/agent/agent_command/__init__.py
```
```

### platform/dirnode/module/agent/agent_command/agent_command.py
```
"""agent_command.py
AgentCommand — responsible for assembling the Copilot CLI command.
"""

from __future__ import annotations

from dirnode.module.agent.agent_command.internal._init_agent_command import _init_agent_command
from dirnode.component.command.command import Command


class AgentCommand:
    """Builds the Copilot CLI command argument list."""

    __slots__ = ("_app", "_which", "_os_name", "_command")

    def __init__(self, app, which=None, os_name=None) -> None:
        self._app = app
        self._which = which
        self._os_name = os_name
        self._command: Command | None = None

    @property
    def command_(self) -> Command:
        if self._command is None:
            self._command = Command([])
        return self._command

    def init_agent_command(self) -> None:
        _init_agent_command(self)
```

### platform/dirnode/module/agent/agent_command/internal/__init__.py
```
```

### platform/dirnode/module/agent/agent_command/internal/_assert_add_dir_exists.py
```

from dirnode.utils.path.path import Path, PathType


def _assert_add_dir_exists(add_dir: PathType) -> None:
    if not Path.is_dir(add_dir):
        raise FileNotFoundError(f"Add directory does not exist: {add_dir}")
```

### platform/dirnode/module/agent/agent_command/internal/_assert_command_set.py
```
def _assert_command_set(command: list | None) -> None:
    if command is None:
        raise ValueError("[AgentCommand] command_ accessed before init_agent_command() was called")
```

### platform/dirnode/module/agent/agent_command/internal/_assert_copilot_cmd_found.py
```
"""_assert_copilot_cmd_found.py
Responsible for one thing: raising FileNotFoundError when the agent CLI binary cannot be located.
"""


def _assert_copilot_cmd_found(command) -> None:
    """Raise FileNotFoundError if command is falsy."""
    if not command:
        raise FileNotFoundError(
            "Agent CLI not found. Set command in app/app.yaml "
            "or ensure the binary is on PATH."
        )
```

### platform/dirnode/module/agent/agent_command/internal/_assert_log_dir_exists.py
```

from dirnode.utils.path.path import Path, PathType


def _assert_log_dir_exists(log_dir: PathType) -> None:
    if not Path.is_dir(log_dir):
        raise FileNotFoundError(f"Log directory does not exist: {log_dir}")
```

### platform/dirnode/module/agent/agent_command/internal/_assert_model_set.py
```
"""_assert_model_set.py
Responsible for one thing: raising ValueError when model app field is missing.
"""


def _assert_model_set(model: str) -> None:
    """Raise ValueError if model is empty."""
    if not model:
        raise ValueError("[build_command] Required app field missing: 'model'")
```

### platform/dirnode/module/agent/agent_command/internal/_assert_output_dir_exists.py
```

from dirnode.utils.path.path import Path, PathType


def _assert_output_dir_exists(output_dir: PathType) -> None:
    if not Path.is_dir(output_dir):
        raise FileNotFoundError(f"Output directory does not exist: {output_dir}")
```

### platform/dirnode/module/agent/agent_command/internal/_create_command.py
```
"""create_command.py
Responsible for one thing: assembling the Copilot CLI command as a list
of arguments ready for subprocess.run.

Requires either app.command or a 'copilot' binary in PATH.
"""

import os
import shutil

from dirnode.module.agent.agent_command.internal._assert_copilot_cmd_found import _assert_copilot_cmd_found
from dirnode.module.agent.agent_command.internal._assert_model_set import _assert_model_set
from dirnode.utils.path.path import Path
from dirnode.constants.constants import DOT_NODE, DIR_OUTPUT, DIR_LOGS


def _create_command(app, which=None, os_name=None) -> list[str]:
    """Build and return the Copilot CLI command argument list.

    Raises FileNotFoundError when the Copilot binary cannot be located.
    which:   optional callable (name: str) -> str | None (defaults to shutil.which).
    os_name: optional str to override os.name for testability.
    """
    if which is None:
        which = shutil.which
    if os_name is None:
        os_name = os.name

    command = which("copilot")
    _assert_copilot_cmd_found(command)

    cmd: list[str] = [command]

    if os_name == "nt" and str(command).lower().endswith((".cmd", ".bat")):
        cmd = ["cmd", "/c"] + cmd
    model = (app.runner_.agent_.agent_properties_.model_ or "").strip()
    _assert_model_set(model)
    cmd.extend(["--model", model])

    cmd.extend(["--allow-all-paths", "--allow-all-tools", "--output-format", "json"])

    if app.cli_.cli_properties_.is_no_ask_user_:
        cmd.append("--no-ask-user")

    if app.cli_.cli_properties_.is_autopilot_:
        cmd.append("--autopilot")

    add_dirs: list[str] = []

    for directory in app.cli_.cli_properties_.add_dirs_:
        d = str(directory).strip()
        if d:
            add_dirs.append(d)

    output_dir = app.app_node_.node_.node_dir_ / DOT_NODE / DIR_OUTPUT
    Path.mkdir(output_dir)
    add_dirs.append(output_dir.as_posix())
    add_dirs.append(app.app_node_.node_.node_dir_.as_posix())

    log_dir = app.app_node_.node_.node_dir_ / DOT_NODE / DIR_LOGS
    Path.mkdir(log_dir)

    for add_dir in add_dirs:
        cmd.extend(["--add-dir", add_dir])
        app.app_trace_.record_info('agent_command._create_command', f'--add-dir {add_dir}')

    cmd.extend(["--log-dir", log_dir.as_posix()])
    app.app_trace_.record_info('agent_command._create_command', f'--log-dir {log_dir.as_posix()}')

    return cmd
```

### platform/dirnode/module/agent/agent_command/internal/_init_agent_command.py
```
from __future__ import annotations

import os
import shutil

from dirnode.module.agent.agent_command.internal._assert_copilot_cmd_found import _assert_copilot_cmd_found
from dirnode.module.agent.agent_command.internal._assert_model_set import _assert_model_set
from dirnode.module.agent.agent_command.internal._assert_output_dir_exists import _assert_output_dir_exists
from dirnode.module.agent.agent_command.internal._assert_log_dir_exists import _assert_log_dir_exists
from dirnode.module.agent.agent_command.internal._assert_add_dir_exists import _assert_add_dir_exists
from dirnode.constants.constants import DOT_NODE, DIR_OUTPUT


def _init_agent_command(agent_command) -> None:
    which = agent_command._which or shutil.which
    os_name = agent_command._os_name or os.name
    app = agent_command._app

    binary = which("copilot")
    _assert_copilot_cmd_found(binary)

    if os_name == "nt" and str(binary).lower().endswith((".cmd", ".bat")):
        agent_command.command_.extend_command_args(["cmd", "/c", binary])
    else:
        agent_command.command_.add_command_arg(binary)

    model = (app.runner_.agent_.agent_properties_.model_ or "").strip()
    _assert_model_set(model)
    agent_command.command_.extend_command_args(["--model", model])

    if app.cli_.cli_properties_.is_allow_all_paths_:
        agent_command.command_.add_command_arg("--allow-all-paths")

    if app.cli_.cli_properties_.is_allow_all_tools_:
        agent_command.command_.add_command_arg("--allow-all-tools")

    agent_command.command_.extend_command_args(["--output-format", app.cli_.cli_properties_.output_format_])


    if app.cli_.cli_properties_.is_no_ask_user_:
        agent_command.command_.add_command_arg("--no-ask-user")

    if app.cli_.cli_properties_.is_autopilot_:
        agent_command.command_.add_command_arg("--autopilot")

    output_dir = app.app_node_.node_.node_dir_ / DOT_NODE / DIR_OUTPUT
    _assert_output_dir_exists(output_dir)
    agent_command.command_.extend_command_args(["--add-dir", str(output_dir)])
    app.app_trace_.record_info('agent_command._init_agent_command', f'--add-dir {output_dir}')

    logs_dir = app.app_node_.node_.node_logs_.logs_dir_
    _assert_log_dir_exists(logs_dir)

    for add_dir in app.cli_.cli_properties_.add_dirs_:
        _assert_add_dir_exists(add_dir)
        agent_command.command_.extend_command_args(["--add-dir", str(add_dir)])
        app.app_trace_.record_info('agent_command._init_agent_command', f'--add-dir {add_dir}')

    node_dir = app.app_node_.node_.node_dir_
    _assert_add_dir_exists(node_dir)
    agent_command.command_.extend_command_args(["--add-dir", str(node_dir)])
    app.app_trace_.record_info('agent_command._init_agent_command', f'--add-dir {node_dir}')

    agent_command.command_.extend_command_args(["--log-dir", str(logs_dir)])
    app.app_trace_.record_info('agent_command._init_agent_command', f'--log-dir {logs_dir}')

```

### platform/dirnode/module/agent/agent_prompt/__init__.py
```
# lib/prompt package
```

### platform/dirnode/module/agent/agent_prompt/agent_prompt.py
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

from dirnode.module.agent.agent_prompt.internal._init_agent_prompt import _init_agent_prompt
from dirnode.module.agent.agent_prompt.internal._build_prompt_from_input import _build_prompt_from_input
from dirnode.component.prompt.prompt_cli.prompt_cli import PromptCli
from dirnode.component.prompt.prompt_role.prompt_role import PromptRole
from dirnode.component.prompt.prompt_skill.prompt_skill import PromptSkill
from dirnode.component.prompt.prompt_system.prompt_system import PromptSystem


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

### platform/dirnode/module/agent/agent_prompt/internal/__init__.py
```
```

### platform/dirnode/module/agent/agent_prompt/internal/_assert_role_resolved.py
```
def _assert_role_resolved(role) -> None:
    if role is None:
        raise ValueError("role is not set — required for prompt_role loading")
```

### platform/dirnode/module/agent/agent_prompt/internal/_assert_role_set.py
```
﻿def _assert_role_set(role) -> None:
    if not role:
        raise ValueError("[init_system_prompt] 'role' is required in app but was not set.")
```

### platform/dirnode/module/agent/agent_prompt/internal/_assert_task_dir_resolved.py
```
def _assert_task_dir_resolved(task_dir) -> None:
    if task_dir is None:
        raise ValueError("task_dir is not set — required for prompt_role loading")
```

### platform/dirnode/module/agent/agent_prompt/internal/_build_from_dir.py
```
from __future__ import annotations


from dirnode.utils.io.io import default_read_utf8_safe
from dirnode.module.agent.agent_prompt.internal._clean_name import _clean_name
from dirnode.utils.path.path import Path, PathType

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

### platform/dirnode/module/agent/agent_prompt/internal/_build_prompt_from_input.py
```
"""_build_prompt_from_input.py
Private. Responsible for one thing: building the full prompt string from
*.md files already loaded into app.app_node_.node_.node_input_.input_files_map_.
"""

from __future__ import annotations

from dirnode.utils.path.path import Path, PathType

from dirnode.module.agent.agent_prompt.internal._clean_name import _clean_name


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

### platform/dirnode/module/agent/agent_prompt/internal/_clean_name.py
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

### platform/dirnode/module/agent/agent_prompt/internal/_create_prompt.py
```
from dirnode.module.agent.agent_prompt.internal._build_prompt_from_input import _build_prompt_from_input
from dirnode.module.agent.agent_prompt.internal._resolve_prompt import _resolve_prompt


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

### platform/dirnode/module/agent/agent_prompt/internal/_find_file.py
```

from dirnode.utils.path.path import Path, PathType


def _find_file(filename: str, node: PathType) -> PathType | None:
    for search_dir in [node / ".node" / "input", node / ".node" / "temp"]:
        if not Path.is_dir(search_dir):
            continue
        for match in Path.rglob(search_dir, filename):
            if Path.is_file(match):
                return match
    return None
```

### platform/dirnode/module/agent/agent_prompt/internal/_has_system_prompt.py
```
"""_has_system_prompt.py
Private. Responsible for one thing: checking whether a system prompt file
for the given role already exists in the input/ directory.
"""

import re

from dirnode.utils.path.path import Path, PathType


def _has_system_prompt(input_dir: PathType, role: str) -> bool:
    if not Path.is_dir(input_dir):
        return False
    pattern = re.compile(rf'^\d{{4}}_system_{re.escape(role)}\.md$')
    return any(pattern.match(f.name) for f in Path.iterdir(input_dir) if Path.is_file(f))
```

### platform/dirnode/module/agent/agent_prompt/internal/_init_agent_prompt.py
```
from __future__ import annotations


from dirnode.module.agent.agent_prompt.internal._assert_task_dir_resolved import _assert_task_dir_resolved
from dirnode.module.agent.agent_prompt.internal._assert_role_resolved import _assert_role_resolved
from dirnode.utils.path.path import Path, PathType
from dirnode.constants.constants import DOT_NODE, DIR_PROMPT


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

### platform/dirnode/module/agent/agent_prompt/internal/_load_role_prompt.py
```
"""_init_role_prompt.py
Private. Responsible for one thing: loading a role prompt file from
role_prompts/<role>.md into the Prompt instance.
"""


from dirnode.utils.path.path import Path, PathType

_ROLE_PROMPTS_DIR = Path.new(__file__).parent.parent / 'role_prompts'


def _init_role_prompt(prompt) -> None:
    role = prompt._app.app_properties_.role_
    if role:
        template = _ROLE_PROMPTS_DIR / f'{role}.md'
        if Path.is_file(template):
            prompt._role_prompt = Path.read_text(template)
```

### platform/dirnode/module/agent/agent_prompt/internal/_resolve_prompt.py
```
from __future__ import annotations


from dirnode.utils.io.io import default_read_utf8_safe
from dirnode.module.agent.agent_prompt.internal._build_from_dir import _build_from_dir
from dirnode.module.agent.agent_prompt.internal._find_file import _find_file
from dirnode.utils.path.path import Path, PathType


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

### platform/dirnode/module/agent/agent_prompt/load_system_prompt.py
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

from dirnode.utils.io.io import default_read_utf8, default_write_utf8
from dirnode.module.agent.agent_prompt.internal._assert_role_set import _assert_role_set
from dirnode.module.agent.agent_prompt.internal._has_system_prompt import _has_system_prompt
from dirnode.utils.path.path import Path, PathType
from dirnode.constants.constants import DOT_NODE, DIR_INPUT

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

### platform/dirnode/module/agent/agent_prompt/role_prompts/analyzer.md
```
You are an **analyzer** agent.
Your role is to analyze the provided input and produce a structured report.
- Identify patterns, problems, and opportunities
- Summarize findings clearly with supporting evidence
- Output a structured markdown report
```

### platform/dirnode/module/agent/agent_prompt/role_prompts/architect.md
```
You are an **architect** agent.
Your role is to design the solution architecture based on the task description.
- Produce a clear architectural blueprint with component diagram (text or ASCII)
- Define interfaces, data flows, and responsibilities of each component
- Output a single markdown architecture document
```

### platform/dirnode/module/agent/agent_prompt/role_prompts/developer.md
```
You are a **developer** agent.
Your role is to implement the solution based on the provided draft or task description.
- Implement all TODOs and stubs left by previous agents
- Write clean, idiomatic, production-quality code
- Add unit tests covering happy path and edge cases
- Output one file per deliverable
```

### platform/dirnode/module/agent/agent_prompt/role_prompts/maker.md
```
You are a **maker** agent.
Your role is to prepare a clear, well-structured draft or scaffold based on the task description.
- Produce a skeleton with correct structure, signatures, and docstrings
- Do not implement the full logic — leave TODOs where implementation is needed
- Output one file per deliverable
- Be concise and precise
```

### platform/dirnode/module/agent/agent_prompt/role_prompts/reviewer.md
```
You are a **reviewer** agent.
Your role is to review the provided code or document for quality, correctness, and completeness.
- Check for bugs, edge cases, and missing error handling
- Verify tests are present and meaningful
- Suggest concrete improvements with code examples
- Output a review report as a single markdown file
```

### platform/dirnode/module/agent/agent_prompt/role_prompts/tester.md
```
You are a **tester** agent.
Your role is to write and execute tests for the provided implementation.
- Write unit tests, integration tests, and edge case tests
- Ensure all tests pass before outputting
- Output test files and a short test report
```

### platform/dirnode/module/agent/agent_properties/__init__.py
```
```

### platform/dirnode/module/agent/agent_properties/agent_properties.py
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

### platform/dirnode/module/router/__init__.py
```
from dirnode.module.router.router.router import Router
```

### platform/dirnode/module/router/router/__init__.py
```
from dirnode.module.router.router.router import Router
```

### platform/dirnode/module/router/router/build_frontmatter.py
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

### platform/dirnode/module/router/router/collect_source_files.py
```

from dirnode.utils.path.path import Path, PathType


def collect_source_files(prev_output_dir: PathType) -> list[PathType]:
    if not Path.is_dir(prev_output_dir):
        return []
    return [f for f in Path.iterdir(prev_output_dir) if Path.is_file(f)]
```

### platform/dirnode/module/router/router/frontmatter.py
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

### platform/dirnode/module/router/router/get_role_to_node_map.py
```
def get_role_to_node_map(pipeline: list) -> dict[str, dict]:
    """Return mapping of role -> node for all nodes that have a role defined."""
    return {n['role']: n for n in pipeline if n.get('role')}
```

### platform/dirnode/module/router/router/get_target_role_from_filename.py
```
from dirnode.utils.path.path import Path, PathType


def get_target_role_from_filename(filename: str, roles: set) -> str | None:
    """Return role if the stem ends with _<role>, else None."""
    stem = Path.new(filename).stem
    parts = stem.rsplit('_', 1)
    if len(parts) == 2 and parts[-1] in roles:
        return parts[-1]
    return None
```

### platform/dirnode/module/router/router/internal/__init__.py
```
```

### platform/dirnode/module/router/router/internal/_assert_active_file_parsed.py
```
from dirnode.utils.path.path import PathType

from dirnode.module.router.router.parse_message_filename import MessageFilename


def _assert_active_file_parsed(parsed: MessageFilename | None, active_file: PathType) -> None:
    if parsed is None:
        raise ValueError(f"[Router] active file has unparseable filename: '{active_file.name}'")
    if not parsed.from_role:
        raise ValueError(f"[Router] active file has no from_role in filename: '{active_file.name}'")
```

### platform/dirnode/module/router/router/internal/_assert_node_in_pipeline.py
```
"""_assert_node_in_pipeline.py
Responsible for one thing: raising ValueError when a node id is not found in the pipeline.
"""


def _assert_node_in_pipeline(index, node_id: str) -> None:
    """Raise ValueError if index is None (node not found in pipeline)."""
    if index is None:
        raise ValueError(f"node '{node_id}' not found in pipeline")
```

### platform/dirnode/module/router/router/internal/_assert_pipeline_node_role_set.py
```
def _assert_pipeline_node_role_set(role: str | None, node_name: str) -> None:
    if not role:
        raise ValueError(f"[Router] pipeline node '{node_name}' has no role defined")
```

### platform/dirnode/module/router/router/internal/_assert_role_set.py
```
"""_assert_role_set.py
Responsible for one thing: raising ValueError when a pipeline node has no role defined.
"""


def _assert_role_set(role: str | None, node: dict) -> None:
    """Raise ValueError if role is falsy."""
    if not role:
        raise ValueError(f"[Router] node '{node.get('id', '?')}' has no role defined")
```

### platform/dirnode/module/router/router/internal/_assert_router_base_set.py
```
def _assert_router_base_set(value) -> None:
    if value is None:
        raise ValueError("router_base not initialized — call init_router() first")
```

### platform/dirnode/module/router/router/internal/_assert_step_within_ttl.py
```
from dirnode.module.router.router.parse_message_filename import MessageFilename


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

### platform/dirnode/module/router/router/internal/_distribute_active.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

from dirnode.structure.pipeline.pipeline.internal._persist_node_status import _persist_node_status
from dirnode.module.router.router.parse_message_filename import increment_step
from dirnode.module.router.router.parse_message_filename import parse_message_filename
from dirnode.status.status import Status
from dirnode.utils.path.path import Path
from dirnode.constants.constants import DOT_NODE, DIR_INPUT

if TYPE_CHECKING:
    from dirnode.module.router.router.router import Router


def _distribute_active(router: 'Router', node_stage, pipeline_nodes, app) -> None:
    active_files = node_stage.get_active_files()
    app.app_trace_.record_info('router._distribute_active', f'distributing {len(active_files)} active file(s)')
    for active_file in active_files:
        active_parsed = parse_message_filename(active_file.name)
        target_role = active_parsed.to_role if active_parsed is not None else None
        target_node = (
            router.router_base_.role_to_node_map_.get(target_role) if target_role
            else router.get_next_pipeline_node()
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
        target_pipeline_node = next(
            (pn for pn in pipeline_nodes if pn.role_ == target_role),
            None,
        ) if target_role else next(
            (pn for pn in pipeline_nodes if pn.mode_ == 'agent'),
            None,
        )
        if target_pipeline_node is not None:
            target_pipeline_node.node_status_.set_status(Status.READY)
            _persist_node_status(target_pipeline_node, app)
            app.app_trace_.record_info(
                'router._run_router._run_router',
                f'node {target_pipeline_node.node_name_} status=READY'
            )
        if active_parsed is not None and active_parsed.msg_type == 'QUESTION':
            node_stage.move_to_pending(active_file.name)
        else:
            node_stage.move_to_history(active_file.name)
```

### platform/dirnode/module/router/router/internal/_expire_pending_ttl.py
```
from __future__ import annotations

from dirnode.module.router.router.parse_message_filename import parse_message_filename


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

### platform/dirnode/module/router/router/internal/_flush_done.py
```
from __future__ import annotations

from dirnode.module.router.router.parse_message_filename import SEPARATOR
from dirnode.module.router.router.parse_message_filename import parse_message_filename
from dirnode.utils.path.path import Path
from dirnode.constants.constants import DOT_NODE, DIR_OUTPUT


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

### platform/dirnode/module/router/router/internal/_init_router.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

from dirnode.module.router.router_base.router_base import RouterBase

if TYPE_CHECKING:
    from dirnode.module.router.router.router import Router


def _init_router(router: 'Router') -> None:
    router.router_base_.init_router_base()
```

### platform/dirnode/module/router/router/internal/_parse_frontmatter.py
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

### platform/dirnode/module/router/router/internal/_pick_active_file.py
```
from dirnode.utils.path.path import PathType
from __future__ import annotations


from dirnode.module.router.router.parse_message_filename import parse_message_filename
from dirnode.constants.constants import DIR_STAGE_ACTIVE


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

### platform/dirnode/module/router/router/internal/_pick_agent_output.py
```
from __future__ import annotations


from dirnode.module.router.router.parse_message_filename import parse_message_filename
from dirnode.module.router.router.internal._assert_pipeline_node_role_set import _assert_pipeline_node_role_set
from dirnode.utils.path.path import Path, PathType
from dirnode.constants.constants import DOT_NODE, DIR_OUTPUT


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
    for pipeline_node in agent_nodes:
        agent_output_dir = pipeline_node.sub_node_properties_.node_dir_ / DOT_NODE / DIR_OUTPUT
        app.app_trace_.record_info('router._pick_agent_output', f'scanning: {agent_output_dir}')
        if not Path.exists(agent_output_dir):
            continue
        role = pipeline_node.role_
        _assert_pipeline_node_role_set(role, pipeline_node.node_name_)
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

### platform/dirnode/module/router/router/internal/_pick_parent_input.py
```
from __future__ import annotations


from dirnode.utils.path.path import Path, PathType
from dirnode.constants.constants import DOT_NODE, DIR_INPUT


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

### platform/dirnode/module/router/router/internal/_rename_parent_input_as_task.py
```
from dirnode.utils.path.path import PathType
from __future__ import annotations


from dirnode.module.router.router.parse_message_filename import SEPARATOR
from dirnode.module.router.router.parse_message_filename import parse_message_filename


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

### platform/dirnode/module/router/router/internal/_route_incoming.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

from dirnode.module.router.router.parse_message_filename import FROM_PLACEHOLDER
from dirnode.module.router.router.parse_message_filename import build_message_filename
from dirnode.module.router.router.parse_message_filename import parse_message_filename
from dirnode.module.router.router.internal._assert_step_within_ttl import _assert_step_within_ttl
from dirnode.module.router.router.internal._distribute_active import _distribute_active
from dirnode.module.router.router_stage.internal._match_pending import _match_pending
from dirnode.utils.path.path import Path, PathType

if TYPE_CHECKING:
    from dirnode.module.router.router.router import Router


def _route_incoming(router: 'Router', node_stage, pipeline_nodes, picked_file: PathType, source_role: str, app) -> None:
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
    _distribute_active(router, node_stage, pipeline_nodes, app)
```

### platform/dirnode/module/router/router/internal/_run_router.py
```
from __future__ import annotations

from typing import TYPE_CHECKING

from dirnode.module.router.router.parse_message_filename import parse_message_filename
from dirnode.module.router.router.internal._expire_pending_ttl import _expire_pending_ttl
from dirnode.module.router.router.internal._flush_done import _flush_done
from dirnode.module.router.router.internal._pick_agent_output import _pick_agent_output
from dirnode.module.router.router.internal._assert_active_file_parsed import _assert_active_file_parsed
from dirnode.module.router.router.internal._pick_active_file import _pick_active_file
from dirnode.module.router.router.internal._pick_parent_input import _pick_parent_input
from dirnode.module.router.router.internal._rename_parent_input_as_task import _rename_parent_input_as_task
from dirnode.module.router.router.internal._route_incoming import _route_incoming
from dirnode.module.router.router.internal._seed_tasker_input_to_first_agent import _seed_tasker_input_to_first_agent

if TYPE_CHECKING:
    from dirnode.module.router.router.router import Router


def _run_router(router: 'Router') -> None:
    app = router._app
    max_step = app.cli_.cli_properties_.max_step_
    node_stage = router.router_stage_.node_stage_

    pipeline_nodes = router.router_base_.pipeline_nodes_
    non_router_nodes = [pn for pn in pipeline_nodes if pn.mode_ != 'router']

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

    _route_incoming(router, node_stage, pipeline_nodes, picked_file, source_role, app)

```

### platform/dirnode/module/router/router/internal/_seed_tasker_input_to_first_agent.py
```
from __future__ import annotations


from dirnode.utils.path.path import Path, PathType
from dirnode.constants.constants import DOT_NODE, DIR_INPUT


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

### platform/dirnode/module/router/router/load_router_params.py
```
﻿"""load_router_params.py — DEPRECATED.
Use app.runner_.router_.init_router() instead.
"""


def load_router_params(app) -> None:
    """Deprecated. Delegates to app.runner_.router_.init_router()."""
    app.runner_.router_.init_router()

```

### platform/dirnode/module/router/router/parse_message_filename.py
```
from __future__ import annotations

from dirnode.utils.path.path import Path, PathType
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

### platform/dirnode/module/router/router/read_metadata_from_file.py
```
from dirnode.utils.path.path import PathType
from __future__ import annotations

from collections.abc import Callable

from dirnode.module.router.router.internal._parse_frontmatter import _parse_frontmatter

from dirnode.utils.io.io import default_read_utf8


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

### platform/dirnode/module/router/router/router.py
```
"""router.py
Router: single entry point for all router-phase operations.

Delegates pipeline state (node order, role map, neighbours) to RouterBase.
Exposes domain-aware methods matching the router phase steps:

    move_prev_output_to_input()  — move previous node output/ → own input/
    copy_input_to_output()       — copy own input/ → own output/, prepend frontmatter
    distribute_output_to_targets() — fan-out own output/ to target nodes' input/

Query helpers (return values, never mutate app):
    get_next_pipeline_node()          — node after current in pipeline (or None)
    get_prev_pipeline_node()          — node before current in pipeline
    get_prev_pipeline_node_role()     — role of previous node
    get_prev_pipeline_node_output_dir() — Path to prev node output/
"""

from __future__ import annotations

import shutil
from collections.abc import Callable
from datetime import datetime

from dirnode.utils.io.io import default_read_utf8, default_write_utf8
from dirnode.module.router.router.build_frontmatter import build_frontmatter
from dirnode.module.router.router.collect_source_files import collect_source_files
from dirnode.module.router.router.parse_message_filename import increment_step
from dirnode.module.router.router.parse_message_filename import parse_message_filename
from dirnode.module.router.router.internal._assert_role_set import _assert_role_set
from dirnode.module.router.router.internal._init_router import _init_router
from dirnode.module.router.router.internal._run_router import _run_router
from dirnode.module.router.router_base.router_base import RouterBase
from dirnode.module.router.router_stage.router_stage import RouterStage
from dirnode.utils.path.path import Path, PathType


class Router:
    """Router for a single node run.

    Resolves pipeline, role map and neighbour nodes once on construction.
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

    def get_next_pipeline_node(self) -> dict | None:
        return self.router_base_.get_next_pipeline_node(self._app.app_node_.node_.node_name_)

    def get_prev_pipeline_node(self) -> dict | None:
        return self.router_base_.get_prev_pipeline_node(self._app.app_node_.node_.node_name_)

    def get_prev_pipeline_node_role(self) -> str:
        """Return the role of the previous node.

        Raises ValueError if 'role' is missing.
        """
        node = self.get_prev_pipeline_node()
        role = node.get("role")
        _assert_role_set(role, node)
        return role

    def get_prev_pipeline_node_output_dir(self, resolve: bool = True) -> PathType:
        """Return the output/ directory of the previous node.

        resolve: when True (default) returns resolved absolute Path.
        """
        p = self._app.app_node_.node_.node_dir_.parent / self.get_prev_pipeline_node().node_name_ / ".node" / "output"
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

        src_dir = self.get_prev_pipeline_node_output_dir()
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

        source_role = self.get_prev_pipeline_node_role()
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

        next_node = self.get_next_pipeline_node()
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
        """Execute the full router pipeline: copy input, build output, distribute."""
        _run_router(self)

    # ------------------------------------------------------------------ #
    # Private                                                              #
    # ------------------------------------------------------------------ #

    def _current_node_index(self) -> int:
        return self.router_base_.get_current_pipeline_node_index(self._app.app_node_.node_.node_name_)
```

### platform/dirnode/module/router/router_base/__init__.py
```
# router_base package
from dirnode.module.router.router_base.router_base import RouterBase
```

### platform/dirnode/module/router/router_base/internal/__init__.py
```
# router_maker internal package
```

### platform/dirnode/module/router/router_base/internal/_assert_node_in_pipeline.py
```
def _assert_node_in_pipeline(index, node_name: str) -> None:
    if index is None:
        raise ValueError(f"node '{node_name}' not found in pipeline")
```

### platform/dirnode/module/router/router_base/internal/_assert_task_md_file_body_set.py
```
def _assert_task_md_file_body_set(value) -> None:
    if value is None:
        raise ValueError("task_md_file_body not loaded — call init_router_base() first")
```

### platform/dirnode/module/router/router_base/internal/_assert_task_yaml_file_body_set.py
```
def _assert_task_yaml_file_body_set(value) -> None:
    if value is None:
        raise ValueError("task_yaml_file_body not loaded — call init_router_base() first")
```

### platform/dirnode/module/router/router_base/internal/_assert_task_yaml_in_task_dir.py
```
from dirnode.utils.path.path import PathType
from __future__ import annotations



def _assert_task_yaml_in_task_dir(yaml_files: list, task_dir: PathType) -> None:
    if not yaml_files:
        raise FileNotFoundError(f"[RouterBase] no .yaml file found in task_dir: {task_dir}")
```

### platform/dirnode/module/router/router_base/internal/_init_router_base.py
```
from __future__ import annotations

from dirnode.module.router.router_base.internal._assert_task_yaml_file_body_set import _assert_task_yaml_file_body_set
from dirnode.module.router.router_base.internal._assert_task_yaml_in_task_dir import _assert_task_yaml_in_task_dir
from dirnode.utils.path.path import Path
from dirnode.constants.constants import DOT_NODE, DIR_TASK


def _init_router_base(router_base, reader=None) -> None:
    task_dir = (router_base._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TASK).resolve()
    yaml_files = Path.glob(task_dir, '*.yaml')
    _assert_task_yaml_in_task_dir(yaml_files, task_dir)
    task_yaml_file_body = Path.read_text(yaml_files[0])
    _assert_task_yaml_file_body_set(task_yaml_file_body)
    router_base._app.app_node_.node_.node_task_._task_yaml_file_body = task_yaml_file_body
    router_base._app.app_node_.node_.node_task_._task_name = yaml_files[0].stem
    router_base.pipeline_.init_pipeline()
```

### platform/dirnode/module/router/router_base/router_base.py
```
"""router_base.py
RouterBase: holds task files loaded from .node/task for every router node.

Slots:
    _app                 — parent App (back-reference)
    _pipeline            — Optional; lazy Pipeline instance
    _role_to_node_map    — dict[role, node] built from pipeline (dict | None)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dirnode.structure.pipeline.pipeline.pipeline import Pipeline
from dirnode.module.router.router_base.internal._assert_node_in_pipeline import _assert_node_in_pipeline
from dirnode.module.router.router_base.internal._init_router_base import _init_router_base


class RouterBase:
    """Holds task files and pipeline state for any router node."""

    __slots__ = ("_app", "_pipeline", "_role_to_node_map")

    def __init__(self, app=None) -> None:
        self._app = app
        self._pipeline = None
        self._role_to_node_map: dict | None = None
    @property
    def pipeline_(self) -> Pipeline:
        if self._pipeline is None:
            self._pipeline = Pipeline(self._app)
        return self._pipeline

    @property
    def pipeline_nodes_(self):
        return self.pipeline_.sub_nodes_

    @property
    def role_to_node_map_(self) -> dict:
        if self._role_to_node_map is None:
            self._role_to_node_map = {n.role_: n for n in self.pipeline_nodes_ if n.role_}
        return self._role_to_node_map

    def get_current_pipeline_node_index(self, node_name: str) -> int:
        index = next(
            (i for i, n in enumerate(self.pipeline_nodes_) if n.node_name_ == node_name),
            None,
        )
        _assert_node_in_pipeline(index, node_name)
        return index

    def get_next_pipeline_node(self, node_name: str):
        index = self.get_current_pipeline_node_index(node_name)
        pipeline_nodes = self.pipeline_nodes_
        return pipeline_nodes[index + 1] if index + 1 < len(pipeline_nodes) else None

    def get_prev_pipeline_node(self, node_name: str):
        index = self.get_current_pipeline_node_index(node_name)
        return self.pipeline_nodes_[index - 1] if index > 0 else None

    def init_router_base(self, reader=None) -> None:
        _init_router_base(self, reader=reader)
```

### platform/dirnode/module/router/router_stage/__init__.py
```
```

### platform/dirnode/module/router/router_stage/internal/__init__.py
```
```

### platform/dirnode/module/router/router_stage/internal/_match_pending.py
```
from dirnode.utils.path.path import PathType
from __future__ import annotations

from typing import TYPE_CHECKING

from dirnode.module.router.router.parse_message_filename import parse_message_filename

if TYPE_CHECKING:
    from dirnode.structure.node.node_stage.node_stage import NodeStage


def _match_pending(node_stage: 'NodeStage', parsed) -> PathType | None:
    if parsed is None or not parsed.thread_id:
        return None
    for pending_file in node_stage.get_pending_files():
        pending_parsed = parse_message_filename(pending_file.name)
        if pending_parsed is not None and pending_parsed.message_id == parsed.message_id:
            return pending_file
    return None
```

### platform/dirnode/module/router/router_stage/router_stage.py
```
from dirnode.utils.path.path import PathType
"""router_stage.py
RouterStage — high-level stage management logic for the router node.

Slots:
    _app — parent App (DOM back-reference)

Delegates all physical I/O to NodeStage via app.app_node_.node_.node_stage_.
"""

from __future__ import annotations


from dirnode.structure.node.node_stage.node_stage import NodeStage


class RouterStage:
    """High-level stage logic for the router — delegates physical I/O to NodeStage."""

    __slots__ = ("_app",)

    def __init__(self, app) -> None:
        self._app = app

    @property
    def node_stage_(self) -> NodeStage:
        return self._app.app_node_.node_.node_stage_
```

### platform/dirnode/module/tasker/__init__.py
```
```

### platform/dirnode/module/tasker/internal/__init__.py
```
```

### platform/dirnode/module/tasker/internal/_assert_first_non_router_node_exists.py
```
from __future__ import annotations


def _assert_first_non_router_node_exists(first_node) -> None:
    if first_node is None:
        raise ValueError("Pipeline has no non-router node — cannot seed task")
```

### platform/dirnode/module/tasker/internal/_assert_router_node_exists.py
```
def _assert_router_node_exists(router_node) -> None:
    if router_node is None:
        raise ValueError(
            "Pipeline configuration error: no router node (mode='router', role != 'maker') found in pipeline"
        )
```

### platform/dirnode/module/tasker/internal/_assert_session_id_set.py
```
def _assert_session_id_set(session_id: str | None) -> None:
    if session_id is None:
        raise RuntimeError('session_id is not set — call _init_task_yaml before accessing session_id_')
```

### platform/dirnode/module/tasker/internal/_assert_task_files_exist.py
```
from dirnode.utils.path.path import PathType
from __future__ import annotations



def _assert_task_files_exist(task_dir: PathType, task_files: list) -> None:
    if not task_files:
        raise FileNotFoundError(f"No *.md files found in task_dir: {task_dir}")
```

### platform/dirnode/module/tasker/internal/_assert_task_md_exists.py
```
"""_assert_task_md_exists.py
Responsible for one thing: raising FileNotFoundError when the task markdown file is missing.
"""

from __future__ import annotations


from dirnode.utils.path.path import Path, PathType


def _assert_task_md_exists(path: PathType) -> None:
    if not Path.is_file(path):
        raise FileNotFoundError(f"[_init_task_md] Task md not found: {path}")
```

### platform/dirnode/module/tasker/internal/_assert_task_pipeline_yaml_exists.py
```
"""_assert_task_pipeline_yaml_exists.py
Responsible for one thing: raising FileNotFoundError when the task pipeline YAML file is missing.
"""

from __future__ import annotations


from dirnode.utils.path.path import Path, PathType


def _assert_task_pipeline_yaml_exists(path: PathType) -> None:
    if not Path.is_file(path):
        raise FileNotFoundError(f"[_validate_task] Task pipeline YAML not found: {path}")
```

### platform/dirnode/module/tasker/internal/_assert_task_pipeline_yaml_valid.py
```
"""_assert_task_pipeline_yaml_valid.py
Responsible for one thing: validating the structure of a loaded pipeline YAML dict.
"""

from __future__ import annotations


def _assert_task_pipeline_yaml_valid(data: dict) -> None:
    """Raise ValueError when pipeline YAML is missing required keys or structure."""
    if not isinstance(data, dict):
        raise ValueError(f"Pipeline YAML must be a mapping, got {type(data).__name__}")
    if 'pipeline' not in data:
        raise ValueError("Pipeline YAML is missing required key: 'pipeline'")
    if not isinstance(data['pipeline'], list):
        raise ValueError(f"Pipeline YAML 'pipeline' must be a list, got {type(data['pipeline']).__name__}")
    if not data['pipeline']:
        raise ValueError("Pipeline YAML 'pipeline' list must not be empty")
    for i, node in enumerate(data['pipeline']):
        for required in ('node_name', 'runner_root_dir', 'role', 'type'):
            if required not in node:
                raise ValueError(f"Pipeline node [{i}] is missing required key: '{required}'")
```

### platform/dirnode/module/tasker/internal/_find_node_with_input.py
```
from __future__ import annotations

from dirnode.utils.path.path import Path
from dirnode.constants.constants import DOT_NODE, DIR_INPUT


def _find_node_with_input(non_router_nodes) -> object | None:
    for pn in non_router_nodes:
        input_dir = pn.sub_node_properties_.node_dir_ / DOT_NODE / DIR_INPUT
        if Path.exists(input_dir) and any(Path.iterdir(input_dir)):
            return pn
    return None
```

### platform/dirnode/module/tasker/internal/_has_own_input.py
```
from __future__ import annotations

from dirnode.utils.path.path import Path
from dirnode.constants.constants import DOT_NODE, DIR_INPUT


def _has_own_input(app) -> bool:
    input_dir = app.app_node_.node_.node_dir_ / DOT_NODE / DIR_INPUT
    return Path.exists(input_dir) and any(Path.iterdir(input_dir))
```

### platform/dirnode/module/tasker/internal/_has_own_output.py
```
from __future__ import annotations

from dirnode.utils.path.path import Path
from dirnode.constants.constants import DOT_NODE, DIR_OUTPUT


def _has_own_output(app) -> bool:
    output_dir = app.app_node_.node_.node_dir_ / DOT_NODE / DIR_OUTPUT
    return Path.exists(output_dir) and any(Path.iterdir(output_dir))
```

### platform/dirnode/module/tasker/internal/_has_router_work.py
```
from __future__ import annotations

from dirnode.utils.path.path import Path
from dirnode.constants.constants import DOT_NODE, DIR_OUTPUT


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

### platform/dirnode/module/tasker/internal/_init_new_node_statuses.py
```
from __future__ import annotations

import yaml

from dirnode.status.status import Status
from dirnode.utils.path.path import Path
from dirnode.constants.constants import DOT_NODE, DIR_TASK


def _init_new_node_statuses(tasker) -> None:
    app = tasker._app
    task_dir = (app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TASK).resolve()
    yaml_files = Path.glob(task_dir, '*.yaml')
    if not yaml_files:
        return
    yaml_path = yaml_files[0]

    initialized_nodes = [pn for pn in tasker.pipeline_.sub_nodes_ if pn.status_ == Status.INITIALIZED]
    if not initialized_nodes:
        return

    data = yaml.safe_load(Path.read_text(yaml_path)) or {}
    for pipeline_node in initialized_nodes:
        for node_dict in data.get('pipeline', []):
            if node_dict.get('node_name') == pipeline_node.node_name_:
                node_dict['status'] = Status.INITIALIZED.name
                break

    Path.write_text(yaml_path, yaml.dump(data, default_flow_style=False, allow_unicode=True))
    app.app_trace_.record_info(
        'tasker._init_new_node_statuses._init_new_node_statuses',
        f'persisted INITIALIZED for {len(initialized_nodes)} new node(s) to {yaml_path.name}'
    )
```

### platform/dirnode/module/tasker/internal/_init_task_md.py
```
from __future__ import annotations

from collections.abc import Callable

from dirnode.utils.io.io import default_read_utf8
from dirnode.utils.path.path import Path, PathType
from dirnode.constants.constants import DOT_NODE, DIR_TASK


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

### platform/dirnode/module/tasker/internal/_init_task_prompts.py
```
from __future__ import annotations


from dirnode.utils.path.path import Path, PathType
from dirnode.constants.constants import DOT_NODE, DIR_TASK


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

### platform/dirnode/module/tasker/internal/_init_task_yaml.py
```
from __future__ import annotations

import yaml
from collections.abc import Callable
from datetime import datetime

from dirnode.utils.io.io import default_read_utf8, default_write_utf8
from dirnode.utils.path.path import Path, PathType
from dirnode.constants.constants import DOT_NODE, DIR_TASK


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

### platform/dirnode/module/tasker/internal/_init_tasker.py
```
from __future__ import annotations

from dirnode.module.tasker.internal._validate_task import _validate_task
from dirnode.module.tasker.internal._seed_pipeline_node_task import _seed_pipeline_node_task


def _init_tasker(tasker, reader=None) -> None:
    _validate_task(tasker._app)
    tasker.pipeline_.init_pipeline()
    _seed_pipeline_node_task(tasker)
```

### platform/dirnode/module/tasker/internal/_move_router_output_to_own.py
```
from __future__ import annotations

from dirnode.utils.path.path import Path
from dirnode.constants.constants import DOT_NODE, DIR_OUTPUT


def _move_router_output_to_own(tasker, app) -> bool:
    sub_nodes = tasker.pipeline_.sub_nodes_
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

### platform/dirnode/module/tasker/internal/_run_iterative_tasker.py
```
from __future__ import annotations

from dirnode.structure.pipeline.pipeline.internal._persist_node_status import _persist_node_status
from dirnode.structure.pipeline.pipeline_node.internal._run_sub_node import _run_sub_node
from dirnode.status.status import Status
from dirnode.module.tasker.internal._seed_task_to_first_node import _seed_task_to_first_node
from dirnode.module.tasker.internal._find_node_with_input import _find_node_with_input
from dirnode.module.tasker.internal._has_router_work import _has_router_work
from dirnode.module.tasker.internal._has_own_output import _has_own_output
from dirnode.module.tasker.internal._has_own_input import _has_own_input
from dirnode.module.tasker.internal._move_router_output_to_own import _move_router_output_to_own
from dirnode.module.tasker.internal._init_task_md import _init_task_md
from dirnode.module.tasker.internal._init_task_yaml import _init_task_yaml
from dirnode.module.tasker.internal._init_task_prompts import _init_task_prompts
from dirnode.utils.path.path import Path
from dirnode.constants.constants import DOT_NODE, DIR_INPUT, DIR_OUTPUT, DIR_TASK

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

        sub_nodes = tasker.pipeline_.sub_nodes_
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

### platform/dirnode/module/tasker/internal/_run_tasker.py
```
from __future__ import annotations

from dirnode.status.status import Status
from dirnode.module.tasker.internal._run_iterative_tasker import _run_iterative_tasker


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

### platform/dirnode/module/tasker/internal/_seed_pipeline_node_task.py
```
from __future__ import annotations

from dirnode.structure.pipeline.pipeline.internal._persist_node_status import _persist_node_status
from dirnode.status.status import Status
from dirnode.module.tasker.internal._assert_router_node_exists import _assert_router_node_exists
from dirnode.utils.path.path import Path
from dirnode.constants.constants import DOT_NODE, DIR_TASK


def _seed_pipeline_node_task(tasker) -> None:
    app = tasker._app

    router_node = next(
        (pn for pn in tasker.pipeline_.sub_nodes_
         if pn.mode_ == 'router'
         and pn.role_ != 'maker'),
        None,
    )
    _assert_router_node_exists(router_node)

    router_node.node_status_.set_status(Status.READY)
    _persist_node_status(router_node, app)
    app.app_trace_.record_info(
        'tasker._seed_pipeline_node_task',
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
        'tasker._seed_pipeline_node_task',
        f'seeded {task_name}.md into {router_node.node_name_} task'
    )
```

### platform/dirnode/module/tasker/internal/_seed_task_to_first_node.py
```
from __future__ import annotations

from dirnode.module.tasker.internal._assert_first_non_router_node_exists import _assert_first_non_router_node_exists
from dirnode.module.tasker.internal._assert_task_files_exist import _assert_task_files_exist
from dirnode.utils.path.path import Path
from dirnode.constants.constants import DOT_NODE, DIR_INPUT


def _seed_task_to_first_node(tasker, task_dir) -> None:
    sub_nodes = tasker.pipeline_.sub_nodes_
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

### platform/dirnode/module/tasker/internal/_validate_task.py
```
"""_validate_task.py
Responsible for one thing: asserting that all required task files exist.
"""

from __future__ import annotations

from dirnode.module.tasker.internal._assert_task_md_exists import _assert_task_md_exists
from dirnode.module.tasker.internal._assert_task_pipeline_yaml_exists import _assert_task_pipeline_yaml_exists
from dirnode.constants.constants import DOT_NODE, DIR_TASK


def _validate_task(app) -> None:
    """Assert that all required task files exist."""
    task_dir = (app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TASK).resolve()
    task_name = app.cli_.cli_properties_.task_name_
    _assert_task_pipeline_yaml_exists(task_dir / f"{task_name}.yaml")
    _assert_task_md_exists(task_dir / f"{task_name}.md")
```

### platform/dirnode/module/tasker/tasker.py
```
"""tasker.py
Tasker: structured runtime state for a single task.

Slots:
    _app         — parent App (DOM back-reference)
    _pipeline              — Pipeline instance (built by init_tasker)
    _session_id            — Optional; session timestamp string (YYYYmmdd_HHMMSS)

Validated properties:
    task_dir_              — resolved Path to node directory (task lives there)
    task_name_             — name derived from node directory name
"""

from __future__ import annotations
from dirnode.structure.pipeline.pipeline.pipeline import Pipeline
from dirnode.status.status import Status
from dirnode.module.tasker.internal._assert_session_id_set import _assert_session_id_set
from dirnode.module.tasker.internal._init_tasker import _init_tasker
from dirnode.module.tasker.internal._run_tasker import _run_tasker


class Tasker:
    """Structured task data for a dirnode pipeline run.

    Constructed lazily and held as app.runner_.tasker_.
    """

    __slots__ = ("_app", "_pipeline", "_session_id")

    def __init__(self, app) -> None:
        self._app = app
        self._pipeline: Pipeline | None = None
        self._session_id: str | None = None

    @property
    def pipeline_(self) -> Pipeline:
        """Return the cached Pipeline instance for this task."""
        if self._pipeline is None:
            self._pipeline = Pipeline(self._app)
        return self._pipeline

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

### platform/dirnode/module/tool/__init__.py
```
```

### platform/dirnode/module/tool/tool/__init__.py
```
from dirnode.module.tool.tool.tool import Tool
```

### platform/dirnode/module/tool/tool/internal/__init__.py
```
```

### platform/dirnode/module/tool/tool/internal/_init_tool.py
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

### platform/dirnode/module/tool/tool/internal/_run_tool.py
```
"""_run_tool.py
Run the external tool defined in config.yaml.

Tools are lightweight executables that do NOT generate working logs.
Builds the subprocess command, runs it, captures output, and returns Status.
"""

from __future__ import annotations

import subprocess

from dirnode.status.status import Status


def _run_tool(tool, runner=None) -> Status:
    if runner is None:
        runner = subprocess.run

    app = tool._app
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
            'tool._run_tool._run_tool',
            f'returncode={proc.returncode}',
            stdout=proc.stdout,
            stderr=proc.stderr,
            returncode=proc.returncode,
        )
        if proc.stderr:
            app.app_trace_.record_warning(
                'tool._run_tool._run_tool',
                Exception(f"stderr (returncode={proc.returncode}): {proc.stderr.strip()}"),
                stdout=proc.stdout,
                stderr=proc.stderr,
                returncode=proc.returncode,
            )
        return Status.from_returncode(proc.returncode)
    except subprocess.TimeoutExpired:
        return Status.from_returncode(2)
    except Exception as exc:
        app.app_trace_.record_error('tool._run_tool._run_tool', exc)
        return Status.from_returncode(1)


def _build_cmd(cfg) -> list[str]:
    return [cfg.command_]
```

### platform/dirnode/module/tool/tool/tool.py
```
"""tool.py
Tool — wrapper for external tools in a pipeline node.

Tools are extra apps that do NOT generate working logs (unlike scripts/workers).

Responsibilities:
    init_tool()   — validate tool fields from node_config
    run_tool()    — build command, run subprocess, return Status
"""

from __future__ import annotations

from collections.abc import Callable
from subprocess import CompletedProcess

from dirnode.module.tool.tool.internal._init_tool import _init_tool
from dirnode.module.tool.tool.internal._run_tool import _run_tool
from dirnode.status.status import Status
from dirnode.module.tool.tool_properties.tool_properties import ToolProperties


class Tool:
    """Runs an external tool process for a single pipeline node."""

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

### platform/dirnode/module/tool/tool_properties/__init__.py
```
```

### platform/dirnode/module/tool/tool_properties/tool_properties.py
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

### platform/dirnode/module/worker/__init__.py
```
from dirnode.module.worker.worker.worker import Worker
```

### platform/dirnode/module/worker/worker/__init__.py
```
from dirnode.module.worker.worker.worker import Worker

__all__ = ["Worker"]
```

### platform/dirnode/module/worker/worker/internal/__init__.py
```
```

### platform/dirnode/module/worker/worker/internal/_init_worker.py
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

### platform/dirnode/module/worker/worker/internal/_run_worker.py
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

from dirnode.status.status import Status


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

### platform/dirnode/module/worker/worker/worker.py
```
"""worker.py
Worker — wrapper for external scripts and processes in a pipeline node.

Responsibilities:
    init_worker()   — validate worker fields from node_config
    run_worker()    — build command, run subprocess, return Status
"""

from __future__ import annotations

from collections.abc import Callable
from subprocess import CompletedProcess

from dirnode.module.worker.worker.internal._init_worker import _init_worker
from dirnode.module.worker.worker.internal._run_worker import _run_worker
from dirnode.status.status import Status
from dirnode.module.worker.worker_properties.worker_properties import WorkerProperties


class Worker:
    """Runs an external script or process for a single pipeline node."""

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

### platform/dirnode/module/worker/worker_properties/__init__.py
```
```

### platform/dirnode/module/worker/worker_properties/worker_properties.py
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

### platform/dirnode/status/__init__.py
```
from dirnode.status.status import Status

__all__ = ["Status"]
```

### platform/dirnode/status/module_status/__init__.py
```
from dirnode.status.module_status.module_status import ModuleStatus
```

### platform/dirnode/status/module_status/module_status/__init__.py
```
from dirnode.status.module_status.module_status.module_status import ModuleStatus
```

### platform/dirnode/status/module_status/module_status/module_status.py
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

### platform/dirnode/status/status/__init__.py
```
from dirnode.status.status.status import Status
```

### platform/dirnode/status/status/status.py
```
"""status.py
Status — semantic result of a pipeline run.

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

### platform/dirnode/structure/__init__.py
```
```

### platform/dirnode/structure/node/__init__.py
```
from dirnode.structure.node.node.node import Node
```

### platform/dirnode/structure/node/node/__init__.py
```
from dirnode.structure.node.node.node import Node
```

### platform/dirnode/structure/node/node/internal/__init__.py
```
```

### platform/dirnode/structure/node/node/internal/_assert_config_yaml_exists.py
```
from __future__ import annotations


from dirnode.utils.path.path import Path, PathType


def _assert_config_yaml_exists(path: PathType) -> None:
    if not Path.is_file(path):
        raise FileNotFoundError(f"[_validate_node] Node config not found: {path}")
```

### platform/dirnode/structure/node/node/internal/_assert_input_dir_exists.py
```
"""_assert_input_dir_exists.py
Responsible for one thing: raising FileNotFoundError when the node input/ directory is missing.
"""

from __future__ import annotations


from dirnode.utils.path.path import Path, PathType


def _assert_input_dir_exists(path: PathType) -> None:
    if not Path.is_dir(path):
        raise FileNotFoundError(f"[_validate_node] Node input/ not found: {path}")
```

### platform/dirnode/structure/node/node/internal/_assert_node_dir_is_dir.py
```
"""_assert_node_dir_is_dir.py
Responsible for one thing: raising FileNotFoundError when a node directory does not exist.
"""

from __future__ import annotations


from dirnode.utils.path.path import Path, PathType


def _assert_node_dir_is_dir(path: PathType, context: str) -> None:
    if not Path.is_dir(path):
        raise FileNotFoundError(f"[{context}] Node directory not found: {path}")
```

### platform/dirnode/structure/node/node/internal/_assert_node_dir_set.py
```
"""_assert_node_dir_set.py
Responsible for one thing: raising ValueError when node_dir is not set.
"""

from __future__ import annotations


def _assert_node_dir_set(node_dir: str | None) -> None:
    if node_dir is None:
        raise ValueError("[Node] node_dir is not set")
```

### platform/dirnode/structure/node/node/internal/_assert_node_name_resolvable.py
```
"""_assert_node_name_resolvable.py
Responsible for one thing: raising ValueError when neither _node_name nor _node_dir is set.
"""


def _assert_node_name_resolvable(node_name: str | None, node_dir: str | None) -> None:
    """Raise ValueError if both node_name and node_dir are falsy."""
    if not node_name and not node_dir:
        raise ValueError("[Node] _node_name is not set and _node_dir is not set")
```

### platform/dirnode/structure/node/node/internal/_assert_source_dir_set.py
```
from dirnode.utils.path.path import PathType
from __future__ import annotations



def _assert_source_dir_set(source_dir: PathType | None) -> None:
    if source_dir is None:
        raise RuntimeError("[Node] source_dir is not set — pass --source-dir to the CLI")
```

### platform/dirnode/structure/node/node/internal/_clean_dir.py
```
"""_clean_dir.py
Remove all files and subdirectories inside a single directory.
"""
from __future__ import annotations

from collections.abc import Callable

from dirnode.utils.path.path import Path, PathType


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

### platform/dirnode/structure/node/node/internal/_clean_input.py
```
"""_clean_input.py
Responsible for one thing: removing all contents of the input/ directory inside a node.
"""

from __future__ import annotations

from collections.abc import Callable

from dirnode.utils.path.path import Path, PathType


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

### platform/dirnode/structure/node/node/internal/_clean_node.py
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

### platform/dirnode/structure/node/node/internal/_clean_output.py
```
"""_clean_output.py
Responsible for one thing: removing all contents of the output/ directory inside a node.
"""

from __future__ import annotations

from collections.abc import Callable

from dirnode.utils.path.path import Path, PathType


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

### platform/dirnode/structure/node/node/internal/_create_node.py
```
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from dirnode.utils.path.path import Path, PathType
from dirnode.constants.constants import DOT_NODE

if TYPE_CHECKING:
    from dirnode.app.app_trace.app_trace import AppTrace

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

### platform/dirnode/structure/node/node/internal/_init_node.py
```
from __future__ import annotations


from dirnode.structure.node.node.internal._validate_node import _validate_node
from dirnode.structure.node.node.internal._assert_source_dir_set import _assert_source_dir_set
from dirnode.utils.path.path import Path, PathType

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

### platform/dirnode/structure/node/node/internal/_validate_node.py
```
from dirnode.utils.path.path import PathType
from __future__ import annotations


from dirnode.structure.node.node.internal._assert_node_dir_is_dir import _assert_node_dir_is_dir
from dirnode.structure.node.node.internal._assert_config_yaml_exists import _assert_config_yaml_exists
from dirnode.structure.node.node.internal._assert_input_dir_exists import _assert_input_dir_exists
from dirnode.constants.constants import DOT_NODE, CONFIG_DIR, CONFIG_YAML, DIR_INPUT


def _validate_node(node_dir: PathType) -> None:
    _assert_node_dir_is_dir(node_dir, '_validate_node')
    _assert_config_yaml_exists(node_dir / DOT_NODE / CONFIG_DIR / CONFIG_YAML)
    _assert_input_dir_exists(node_dir / DOT_NODE / DIR_INPUT)
```

### platform/dirnode/structure/node/node/node.py
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

from dirnode.structure.node.node.internal._init_node import _init_node
from dirnode.structure.node.node.internal._clean_node import _clean_node
from dirnode.structure.node.node.internal._assert_node_dir_set import _assert_node_dir_set
from dirnode.structure.node.node_archive.node_archive import NodeArchive
from dirnode.structure.node.node_config.node_config import NodeConfig
from dirnode.structure.node.node_input.node_input import NodeInput
from dirnode.structure.node.node_output.node_output import NodeOutput
from dirnode.structure.node.node_prompt.node_prompt import NodePrompt
from dirnode.structure.node.node_logs.node_logs import NodeLogs
from dirnode.structure.node.node_scripts.node_scripts import NodeScripts
from dirnode.structure.node.node_task.node_task import NodeTask
from dirnode.structure.node.node_status.node_status import NodeStatus
from dirnode.structure.node.node_stage.node_stage import NodeStage
from dirnode.structure.node.node_temp.node_temp import NodeTemp
from dirnode.status.status import Status

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

### platform/dirnode/structure/node/node_archive/__init__.py
```
# dirnode/node_archive package
from dirnode.structure.node.node_archive.node_archive import NodeArchive
__all__ = ['NodeArchive']
```

### platform/dirnode/structure/node/node_archive/internal/__init__.py
```
```

### platform/dirnode/structure/node/node_archive/internal/_clean_node_archive.py
```
from __future__ import annotations

from dirnode.utils.path.path import Path


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

### platform/dirnode/structure/node/node_archive/internal/_save_archive_zip.py
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

from dirnode.utils.path.path import Path, PathType

if TYPE_CHECKING:
    from dirnode.app.app_trace.app_trace import AppTrace

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

### platform/dirnode/structure/node/node_archive/node_archive.py
```
from dirnode.utils.path.path import PathType
"""node_archive.py  (node_archive)
NodeArchive — single entry point for all node archive operations.

Slots:
    _app            — parent App
    _module_status  — ModuleStatus enum; NEW on construction, INIT after init_node_archive()

Methods:
    save_archive(clock)     — write archive ZIP; never raises
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from dirnode.status.module_status.module_status import ModuleStatus
from dirnode.structure.node.node_archive.internal._save_archive_zip import _save_archive_zip
from dirnode.structure.node.node_archive.internal._clean_node_archive import _clean_node_archive
from dirnode.constants.constants import DOT_NODE, DIR_ARCHIVE


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

### platform/dirnode/structure/node/node_config/__init__.py
```
from dirnode.structure.node.node_config.node_config import NodeConfig

__all__ = ["NodeConfig"]
```

### platform/dirnode/structure/node/node_config/internal/__init__.py
```
```

### platform/dirnode/structure/node/node_config/internal/_init_node_config.py
```
﻿"""_init_node_config.py
Private. Responsible for one thing: reading config.yaml into NodeConfig._config.
"""

from __future__ import annotations

from dirnode.app.app.app import App


def _init_node_config(app: App) -> None:
    app.node_config_.init_node_config()
```

### platform/dirnode/structure/node/node_config/node_config.py
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

import yaml


from dirnode.utils.io.io import default_read_utf8, default_write_utf8
from dirnode.component.config.config.config import Config
from dirnode.status.module_status.module_status import ModuleStatus
from dirnode.utils.path.path import Path, PathType
from dirnode.constants.constants import DOT_NODE, CONFIG_DIR, CONFIG_YAML

_PIPELINE_ONLY_KEYS = frozenset({'node_name', 'parent_node_dir', 'status'})


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
            raise ValueError("[NodeConfig] config not initialized — call init_node_config() first")
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
        self._config = Config(self._app)
        self._config.init_config(cfg_path, source='node')
        self._module_status = ModuleStatus.INIT

    def append_node_config(self, node_dir: PathType, config_dict: dict, runner_root_dir: str, overwrite: bool = False, writer=None, reader=None) -> None:
        if writer is None:
            writer = default_write_utf8
        if reader is None:
            reader = default_read_utf8
        cfg_path = node_dir / DOT_NODE / CONFIG_DIR / CONFIG_YAML
        existing: dict = {}
        if Path.is_file(cfg_path):
            existing = yaml.safe_load(reader(cfg_path)) or {}
        else:
            default_path = Path.new(runner_root_dir) / CONFIG_DIR / CONFIG_YAML
            if Path.is_file(default_path):
                existing = yaml.safe_load(reader(default_path)) or {}
        updates = {k: v for k, v in config_dict.items() if k not in _PIPELINE_ONLY_KEYS}
        if overwrite:
            existing.update(updates)
        else:
            for k, v in updates.items():
                if k not in existing:
                    existing[k] = v
        body = yaml.dump(existing, default_flow_style=False, allow_unicode=True)
        writer(cfg_path, body)
        self._config = Config(self._app)
        for k, v in existing.items():
            self._config.append_config_value(k, v, 'root')
        self._module_status = ModuleStatus.INIT
```

### platform/dirnode/structure/node/node_input/__init__.py
```
# dirnode/node_input package
from dirnode.structure.node.node_input.node_input import NodeInput
__all__ = ['NodeInput']
```

### platform/dirnode/structure/node/node_input/internal/__init__.py
```
# input internal package
```

### platform/dirnode/structure/node/node_input/internal/_assert_input_dir_exists.py
```
"""_assert_input_dir_exists.py
Validate that the input directory exists and is a directory.
"""

from __future__ import annotations


from dirnode.utils.path.path import Path, PathType


def _assert_input_dir_exists(input_dir: PathType) -> None:
    if not Path.is_dir(input_dir):
        raise ValueError(f"Input directory does not exist or is not a directory: {input_dir}")
```

### platform/dirnode/structure/node/node_input/internal/_init_node_input.py
```
from __future__ import annotations

from dirnode.utils.file.File import File
from dirnode.utils.file.internal._assert_suffix_allowed import _ALLOWED_SUFFIXES
from dirnode.structure.node.node_input.internal._assert_input_dir_exists import _assert_input_dir_exists
from dirnode.utils.path.path import Path
from dirnode.constants.constants import DOT_NODE, DIR_INPUT


def _init_node_input(node_input) -> None:
    node_input._input_dir = (node_input._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_INPUT).resolve()
    _assert_input_dir_exists(node_input._input_dir)
    node_input._input_files_map = {}
    for path in sorted(p for p in Path.iterdir(node_input.input_dir_) if Path.is_file(p) and p.suffix.lower() in _ALLOWED_SUFFIXES):
        file = File(path)
        file.read_file()
        node_input._input_files_map[file] = path.name
```

### platform/dirnode/structure/node/node_input/node_input.py
```
"""node_input.py
NodeInput: single entry point for reading node input files.

Fields (own):
    input_dir        — path to the input directory (Path)
    input_files_map  — dict[File, str] mapping each loaded File to its file_name
    _module_status   — ModuleStatus enum; NEW on construction, INIT after init_node_input()

Methods:
    init_node_input() — load all *.md files from input_dir into input_files_map
"""

from __future__ import annotations


from dirnode.utils.file.File import File
from dirnode.status.module_status.module_status import ModuleStatus
from dirnode.structure.node.node_input.internal._init_node_input import _init_node_input
from dirnode.utils.path.path import Path, PathType


class NodeInput:
    """Manages reading of input files for a single node run.

    input_dir must be set before calling init_input.
    init_input loads all *.md files from input_dir into input_files_map.
    """

    __slots__ = ("_app", "_input_dir", "_input_files_map", "_module_status")

    def __init__(self, app) -> None:
        self._app = app
        self._input_dir: PathType | None = None
        self._input_files_map: dict[File, str] = {}
        self._module_status: ModuleStatus = ModuleStatus.NEW

    # -----------------------------------------------------------------------
    # Validated properties
    # -----------------------------------------------------------------------

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

### platform/dirnode/structure/node/node_logs/__init__.py
```
# dirnode/node_logs package
from dirnode.structure.node.node_logs.node_logs import NodeLogs
__all__ = ['NodeLogs']
```

### platform/dirnode/structure/node/node_logs/internal/__init__.py
```
# dirnode/node_logs/internal package
```

### platform/dirnode/structure/node/node_logs/internal/_clean_node_logs.py
```
from __future__ import annotations

from dirnode.utils.path.path import Path


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

### platform/dirnode/structure/node/node_logs/internal/_init_node_logs.py
```
from __future__ import annotations
from dirnode.constants.constants import DOT_NODE, DIR_LOGS


def _init_node_logs(node_logs) -> None:
    node_logs._logs_dir = (node_logs._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_LOGS).resolve()
```

### platform/dirnode/structure/node/node_logs/node_logs.py
```
from dirnode.utils.path.path import PathType
"""node_logs.py
NodeLogs: manages the logs directory for a single node run.

Slots:
    _app            — parent App
    _module_status  — ModuleStatus enum; NEW on construction, INIT after init_node_logs()
"""

from __future__ import annotations


from dirnode.status.module_status.module_status import ModuleStatus
from dirnode.structure.node.node_logs.internal._clean_node_logs import _clean_node_logs
from dirnode.structure.node.node_logs.internal._init_node_logs import _init_node_logs


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

### platform/dirnode/structure/node/node_output/__init__.py
```
# dirnode/node_output package
from dirnode.structure.node.node_output.node_output import NodeOutput
__all__ = ['NodeOutput']
```

### platform/dirnode/structure/node/node_output/internal/__init__.py
```
# output internal package
```

### platform/dirnode/structure/node/node_output/internal/_assert_output_dir_exists.py
```
"""_assert_output_dir_exists.py
Validate that the output directory exists and is a directory.
"""

from __future__ import annotations


from dirnode.utils.path.path import Path, PathType


def _assert_output_dir_exists(output_dir: PathType) -> None:
    if not Path.is_dir(output_dir):
        raise ValueError(f"Output directory does not exist or is not a directory: {output_dir}")
```

### platform/dirnode/structure/node/node_output/internal/_clean_node_output.py
```
from __future__ import annotations


from dirnode.utils.path.path import Path, PathType


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

### platform/dirnode/structure/node/node_output/internal/_init_node_output.py
```
from __future__ import annotations
from dirnode.constants.constants import DOT_NODE, DIR_OUTPUT


def _init_node_output(node_output) -> None:
    node_output._output_dir = (node_output._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_OUTPUT).resolve()
```
