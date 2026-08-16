"""SeedProvider — contract for per-BC database seeding.

Each bounded context owns its seed data and implements this protocol.
The platform only defines the contract; it never imports a bounded context.
"""

from __future__ import annotations

from typing import Protocol


class SeedProvider(Protocol):
    """Idempotent database seeding for a single bounded context.

    Implementations must be safe to call repeatedly against the same
    database URL: base data and dev data insert records only when they
    are missing.
    """

    async def bootstrap_database(self, url: str, reset_db: bool = False) -> None:
        """Create the schema and insert base/required data."""
        ...

    async def seed_dev_data(self, url: str) -> None:
        """Insert realistic development/demo data on top of base data."""
        ...


__all__ = ["SeedProvider"]
