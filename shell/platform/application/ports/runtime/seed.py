from __future__ import annotations

from typing import Protocol


class SeedProvider(Protocol):
    async def bootstrap_database(self, url: str, reset_db: bool = False) -> None: ...

    async def seed_dev_data(self, url: str) -> None: ...


__all__ = ["SeedProvider"]
