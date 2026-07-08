from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RagDocumentGetByIdQuery:
    document_id: str
