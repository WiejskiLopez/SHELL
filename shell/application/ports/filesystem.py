from __future__ import annotations

from typing import Protocol


class TaskExecutionLoader(Protocol):
    async def load(self, md_path: str) -> str: ...
