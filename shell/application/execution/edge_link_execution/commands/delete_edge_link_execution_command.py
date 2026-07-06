from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeleteEdgeLinkExecutionCommand:
    id: str

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("id cannot be empty")
