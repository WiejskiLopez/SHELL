from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.events import IntegrationEvent


@dataclass(frozen=True, slots=True)
class NodeLinkExecutionUpdatedIntegrationEvent(IntegrationEvent):
    node_link_execution_id: str
