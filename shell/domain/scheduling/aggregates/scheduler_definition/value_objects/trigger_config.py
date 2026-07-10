from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shell.platform.domain.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class TriggerConfig(ValueObject):
    source_context: str
    trigger_event_type: str
    trigger_filter: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.source_context:
            raise ValueError("TriggerConfig.source_context cannot be empty")
        if not self.trigger_event_type:
            raise ValueError("TriggerConfig.trigger_event_type cannot be empty")

    def __str__(self) -> str:
        return f"TriggerConfig({self.source_context}/{self.trigger_event_type})"
