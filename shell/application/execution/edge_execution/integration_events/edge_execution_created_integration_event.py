from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.events import IntegrationEvent


@dataclass(frozen=True, slots=True)
class EdgeExecutionCreatedIntegrationEvent(IntegrationEvent):
    edge_execution_id: str
    edge_definition_id: str
    source_node_execution_id: str
    target_node_execution_id: str | None
