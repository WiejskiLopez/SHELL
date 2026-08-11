from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateProjectCommand:
    name: str
    repo_url: str | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name cannot be empty")
