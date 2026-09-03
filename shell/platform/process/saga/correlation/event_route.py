"""EventRoute — mapowanie przychodzącego eventu na instancję sagi."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from shell.platform.application.events.integration_event import IntegrationEvent


@dataclass(frozen=True, slots=True)
class EventRoute:
    """Trasa: event → instancja sagi (start albo kontynuacja)."""

    saga_type: str
    extract_key: Callable[[IntegrationEvent], str]
    on_new_instance: bool = False
