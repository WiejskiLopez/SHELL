from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


@dataclass(frozen=True, slots=True)
class SagaTimedOut:
    saga_id: str
    saga_key: str
    step: str
    payload: Mapping[str, object] = field(default_factory=dict)
