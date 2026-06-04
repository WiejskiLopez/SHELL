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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.app.app.app import App


class Worker:
    """Runs an external script or process for a single graph node."""

    __slots__ = ("_app", "_script_file_body", "_worker_properties")

    def __init__(self, app: 'App') -> None:
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
