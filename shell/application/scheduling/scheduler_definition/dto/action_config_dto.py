from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ActionConfigDto:
    graph_definition_id: str | None = None
    input_mapping: str | None = None
    emit_event_type: str | None = None
    emit_event_payload: str | None = None

