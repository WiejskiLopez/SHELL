from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.value_objects.ids import EnvelopeEventId


@dataclass(slots=True)
class EnvelopeEvent:
    id: EnvelopeEventId
    kind: str
    payload: dict[str, object]
    created_at: datetime
