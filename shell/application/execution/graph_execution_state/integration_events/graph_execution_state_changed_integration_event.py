from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.events import IntegrationEvent


@dataclass(frozen=True, slots=True)
class GraphExecutionStateChangedIntegrationEvent(IntegrationEvent):
    graph_execution_id: str
    graph_execution_state_id: str
