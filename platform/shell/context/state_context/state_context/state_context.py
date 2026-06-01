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
