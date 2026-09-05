from __future__ import annotations


class ConcurrentModificationError(RuntimeError):
    """Raised when a saga snapshot has an obsolete version."""

    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(f"Concurrent modification of {resource}: {identifier}")
