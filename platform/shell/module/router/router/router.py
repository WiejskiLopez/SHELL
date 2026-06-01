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
