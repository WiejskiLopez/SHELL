from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IndexDocumentCommand:
    source_uri: str
    title: str
    domain: str
    text: str
    chunk_size: int = 500
    overlap: int = 50

    def __post_init__(self) -> None:
        if not self.source_uri:
            raise ValueError("source_uri cannot be empty")
        if not self.title:
            raise ValueError("title cannot be empty")
