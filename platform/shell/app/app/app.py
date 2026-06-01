"""app.py
App — central runtime state for a shell graph run.

Holds typed references to all module objects and flat configuration values.
Module objects are lazily initialized on first access via properties.
"""

from __future__ import annotations

from typing import Any

from shell.app.app_node.app_node import AppNode
from shell.component.cli.cli.cli import Cli
from shell.component.manifest.manifest import Manifest
from shell.component.config.config.config import Config
from shell.component.placeholders.placeholders import Placeholders
from shell.app.app_trace.app_trace import AppTrace
from shell.app.app_properties.app_properties import AppProperties
from shell.component.result.result import Result
from shell.app.app_runner.app_runner import AppRunner
from shell.component.runtime.runtime.runtime import Runtime
from shell.memory.memory.memory import Memory
from shell.bus.message_bus.message_bus import MessageBus
from shell.bus.workflow_state.workflow_state import WorkflowState
from shell.task.task_repo.task_repo import TaskRepo
from shell.app.app.internal._init_app import _init_app
from shell.app.app.internal._init_memory_and_bus import _init_memory_and_bus
from shell.app.app.internal._run_app import _run_app
from shell.app.app.internal._append_app_config import _append_app_config

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_REPR_FIELDS: tuple[str, ...] = ('_result', '_runner')


class App:
    __slots__ = (
        # Private backing slots for module object properties
        '_app_node', '_runner',
        '_cli', '_app_config',
        '_result', '_app_trace',
        '_placeholders',
        '_app_properties',
        '_runtime',
        '_memory', '_bus', '_workflow_state', '_task_repo',
    )

    def __init__(self) -> None:
        self._app_node: AppNode | None = None
        self._runner: AppRunner | None = None
        self._cli: Cli | None = None
        self._app_config: Config | None = None
        self._result: Result | None = None
        self._app_trace: AppTrace | None = None
        self._placeholders: Placeholders | None = None
        self._app_properties: AppProperties | None = None
        self._runtime: Runtime | None = None
        self._memory: Memory | None = None
        self._bus: MessageBus | None = None
        self._workflow_state: WorkflowState | None = None
        self._task_repo: TaskRepo | None = None

    # -----------------------------------------------------------------------
    # Repr
    # -----------------------------------------------------------------------

    def __repr__(self) -> str:
        pairs = ", ".join(
            f"{k}={getattr(self, k)!r}" for k in _REPR_FIELDS
            if getattr(self, k) is not None
        )
        return f"App({pairs})"

    # -----------------------------------------------------------------------
    # Result facade (backward-compat delegating properties)
    # Fields now live in Result but accessed via App for compat.
    # -----------------------------------------------------------------------

    @property
    def result_(self) -> Result:
        """Return the Result singleton for this run."""
        if self._result is None:
            self._result = Result(self)
        return self._result

    @property
    def app_trace_(self) -> AppTrace:
        """Return the AppTrace instance for this run."""
        if self._app_trace is None:
            self._app_trace = AppTrace(self)
        return self._app_trace

    # -----------------------------------------------------------------------
    # Runner facade
    # -----------------------------------------------------------------------

    @property
    def runner_(self) -> AppRunner:
        """Return the cached Runner for this app."""
        if self._runner is None:
            self._runner = AppRunner(self)
        return self._runner

    # AppNode facade
    # -----------------------------------------------------------------------

    @property
    def app_node_(self) -> AppNode:
        """Return the cached AppNode instance for this app."""
        if self._app_node is None:
            self._app_node = AppNode(self)
        return self._app_node


    # AppConfiguration facade
    # -----------------------------------------------------------------------

    @property
    def cli_(self) -> Cli:
        if self._cli is None:
            self._cli = Cli(self)
        return self._cli

    @property
    def manifest_(self) -> Manifest:
        return self.runtime_.manifest_

    @property
    def runtime_(self) -> Runtime:
        if self._runtime is None:
            self._runtime = Runtime(self)
        return self._runtime

    @property
    def app_config_(self) -> Config:
        if self._app_config is None:
            self._app_config = Config(self)
        return self._app_config

    @property
    def placeholders_(self) -> Placeholders:
        if self._placeholders is None:
            self._placeholders = Placeholders(self)
        return self._placeholders

    @property
    def app_properties_(self) -> AppProperties:
        if self._app_properties is None:
            self._app_properties = AppProperties(self)
        return self._app_properties

    # -----------------------------------------------------------------------
    # Memory / Bus / WorkflowState facades
    # -----------------------------------------------------------------------

    @property
    def memory_(self) -> Memory:
        if self._memory is None:
            self._memory = Memory()
        return self._memory

    @property
    def bus_(self) -> MessageBus:
        if self._bus is None:
            self._bus = MessageBus()
        return self._bus

    @property
    def workflow_state_(self) -> WorkflowState:
        if self._workflow_state is None:
            self._workflow_state = WorkflowState()
        return self._workflow_state

    @property
    def task_repo_(self) -> TaskRepo:
        if self._task_repo is None:
            self._task_repo = TaskRepo()
        return self._task_repo

    def init_memory_and_bus(self) -> None:
        _init_memory_and_bus(self)

    # -----------------------------------------------------------------------
    # Phase methods
    # -----------------------------------------------------------------------

    @classmethod
    def init_app(
        cls,
        argv: list[str] | None = None,
        mode: str | None = None,
        runner_root_dir: str | None = None,
        # --- test seams (injectable overrides) ---
        *,
        make_dirs=None,
        version_info: tuple[int, ...] | None = None,
        locker=None,
    ) -> App:
        return _init_app(
            cls,
            argv=argv,
            mode=mode,
            runner_root_dir=runner_root_dir,
            make_dirs=make_dirs,
            version_info=version_info,
            locker=locker,
        )

    def run_app(self) -> int:
        return _run_app(self)

    def append_app_config(self, config_dict: dict, source: str) -> None:
        _append_app_config(self, config_dict, source)

