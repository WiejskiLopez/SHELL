from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.base.value_object import ValueObject
from shell.platform.domain.exceptions.domain_error import DomainError

if TYPE_CHECKING:
    from shell.platform.types import JsonStr


@dataclass(frozen=True, slots=True)
class TriggerConfig(ValueObject):
    source_context: str
    trigger_event_type: str
    trigger_filter: JsonStr | None = None

    def __post_init__(self) -> None:
        if not self.source_context:
            raise DomainError("TriggerConfig.source_context cannot be empty")
        if not self.trigger_event_type:
            raise DomainError("TriggerConfig.trigger_event_type cannot be empty")

    def __str__(self) -> str:
        return f"TriggerConfig({self.source_context}/{self.trigger_event_type})"
