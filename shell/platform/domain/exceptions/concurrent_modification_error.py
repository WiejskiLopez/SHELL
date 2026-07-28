from __future__ import annotations

from shell.platform.domain.exceptions.domain_error import DomainError


class ConcurrentModificationError(DomainError):
    """Aggregate został współbieżnie zmodyfikowany — wersja nie zgadza się przy zapisie."""

    def __init__(self, aggregate_name: str, aggregate_id: str) -> None:
        super().__init__(
            f"{aggregate_name} was concurrently modified: id={aggregate_id!r}",
        )
