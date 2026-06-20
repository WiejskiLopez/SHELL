from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TriggerConfig:
    source_context: str
    trigger_event_type: str
    trigger_filter: dict | None = None
