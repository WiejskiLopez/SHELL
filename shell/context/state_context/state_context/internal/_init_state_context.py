from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.context.state_context.state_context.state_context import StateContext


def _init_state_context(state_context: StateContext) -> None:
    state_context._workflow_id = ""
    state_context._current_node = ""
    state_context._previous_node = ""
    state_context._next_node = ""
