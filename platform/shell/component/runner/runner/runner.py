"""runner.py
Runner — domain methods shared by all runner types.

Owns _app, _agent, _mode and _runner_properties slots.

Domain methods (per spec):
    run_runner(timer)    — dispatch CLI flags to the appropriate domain method
"""

from __future__ import annotations

from shell.module.agent.agent.agent import Agent
from shell.module.router.router.router import Router
from shell.component.runner.runner.internal._init_runner import _init_runner
from shell.component.runner.runner.internal._run_runner import _run_runner
from shell.component.runner.runner_properties.runner_properties import RunnerProperties
from shell.module.tasker.tasker import Tasker
from shell.module.tool.tool import Tool
from shell.module.worker.worker.worker import Worker

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

