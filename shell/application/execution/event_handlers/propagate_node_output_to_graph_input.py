"""PropagateNodeOutputToGraphInput — legacy handler, obecnie nieużywany.

Zamysł: po zakończeniu NodeExecution kopiował output noda do stanu
GraphExecution (GraphExecutionState z direction=IN). W praktyce nikt
nie odczytuje tego stanu, więc handler jest martwy.

TODO: usunąć wraz z rejestracją w event_container.py jeśli potwierdzimy
że żaden inny handler nie polega na GraphExecutionState z kierunkiem IN
tworzonym przez ten handler.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.node_execution.events.node_execution_completed_event import (
        NodeExecutionCompletedEvent,
    )


class PropagateNodeOutputToGraphInput:
    async def handle(
        self, node_execution_completed_event: NodeExecutionCompletedEvent
    ) -> None:
        pass
