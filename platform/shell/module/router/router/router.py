"""router.py
Router: bus-based routing pass for a single graph.

Resolves graph + role map via RouterBase. Single domain method run_router()
delegates to _run_router which:
- expires envelopes past max_step (stage -> DEAD)
- moves PENDING envelopes to ACTIVE by resolving target_role -> receiver_node_id

All FS-based stage shuffling has been removed (see shell/bus/ for the bus).
"""

from __future__ import annotations

from shell.module.router.router.internal._init_router import _init_router
from shell.module.router.router.internal._run_router import _run_router
from shell.module.router.router_base.router_base import RouterBase


class Router:
    """Routing decisions on the bus for a single node run."""

    __slots__ = ("_app", "_router_base")

    def __init__(self, app) -> None:
        self._app = app
        self._router_base: RouterBase | None = None

    @property
    def router_base_(self) -> RouterBase:
        if self._router_base is None:
            self._router_base = RouterBase(self._app)
        return self._router_base

    def init_router(self) -> None:
        _init_router(self)

    def run_router(self) -> None:
        _run_router(self)
