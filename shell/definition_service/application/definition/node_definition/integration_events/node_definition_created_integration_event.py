from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.events import IntegrationEvent


@dataclass(frozen=True, slots=True)
class NodeDefinitionCreatedIntegrationEvent(IntegrationEvent):
    node_definition_id: str
