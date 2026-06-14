"""Prompt aggregate."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell_ddd.domain.value_objects.hash import Hash

if TYPE_CHECKING:
    from datetime import datetime

    from shell_ddd.domain.value_objects.ids import PromptId


@dataclass(slots=True)
class Prompt:
    id: PromptId
    name: str
    version: int
    hash: Hash
    body: str
    source_uri: str
    is_current: bool
    created_at: datetime

    @classmethod
    def new(
        cls,
        *,
        id_: PromptId,
        name: str,
        body: str,
        source_uri: str = "",
        now: datetime,
    ) -> Prompt:
        return cls(
            id=id_,
            name=name,
            version=1,
            hash=Hash.of(body),
            body=body,
            source_uri=source_uri,
            is_current=True,
            created_at=now,
        )
