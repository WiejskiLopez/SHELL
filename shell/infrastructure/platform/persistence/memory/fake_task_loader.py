from __future__ import annotations


class FakeTaskLoader:
    def __init__(self, md: str = "# Task") -> None:
        self._md = md

    async def load(self, md_path: str) -> str:
        return self._md
