from __future__ import annotations

from typing import Protocol


class TokenGenerator(Protocol):
    def generate(self) -> str: ...
