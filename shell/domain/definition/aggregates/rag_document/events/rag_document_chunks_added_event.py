from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.definition.value_objects.ids import RagDocumentId
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class RagDocumentChunksAddedEvent(DomainEvent):
    document_id: RagDocumentId
    chunk_count: int
    model: str

    @classmethod
    def now(cls, document_id: RagDocumentId, chunk_count: int, model: str, now: datetime) -> RagDocumentChunksAddedEvent:
        return cls(occurred_at=now, document_id=document_id, chunk_count=chunk_count, model=model)

    @classmethod
    def from_payload(cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            document_id=RagDocumentId(payload.get("document_id")),
            chunk_count=payload.get("chunk_count", 0),
            model=payload.get("model", ""),
        )
