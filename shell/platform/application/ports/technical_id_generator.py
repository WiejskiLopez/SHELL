from __future__ import annotations

from typing import Protocol


class TechnicalIdGenerator(Protocol):
    def new_id(self) -> str: ...
