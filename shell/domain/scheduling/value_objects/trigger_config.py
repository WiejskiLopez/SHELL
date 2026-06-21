from __future__ import annotations

from dataclasses import dataclass

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class TriggerConfig(ValueObject):
    source_context: str
    trigger_event_type: str
    trigger_filter: dict | None = None
