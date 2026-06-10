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
