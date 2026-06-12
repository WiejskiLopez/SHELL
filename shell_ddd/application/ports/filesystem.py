from __future__ import annotations
from typing import Protocol


class TaskLoader(Protocol):
    async def load(self, md_path: str) -> str: ...
