from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ActionConfig:
    action_type: str
    graph_definition_id: str | None = None
    input_mapping: dict | None = None
    emit_event_type: str | None = None
    emit_event_payload: dict | None = None
