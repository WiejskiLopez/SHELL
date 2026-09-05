from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass(frozen=True, slots=True)
class EventRoute:
    saga_type: str
    extract_key: Callable[[object], str]
    on_new_instance: bool = False
