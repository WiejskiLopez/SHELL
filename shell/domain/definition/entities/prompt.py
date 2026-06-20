"""Prompt entity."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.platform.base.entity import Entity
from shell.domain.platform.value_objects.hash import Hash
from shell.domain.definition.value_objects.ids import PromptId

if TYPE_CHECKING:
    from datetime import datetime


class Prompt(Entity[PromptId]):
    __slots__ = ("name", "version", "hash", "body", "source_uri", "is_current", "created_at")

    def __init__(
        self,
        id: PromptId,
        name: str,
        version: int,
        hash: Hash,
        body: str,
        source_uri: str,
        is_current: bool,
        created_at: datetime,
    ) -> None:
        super().__init__(id)
        self.name = name
        self.version = version
        self.hash = hash
        self.body = body
        self.source_uri = source_uri
        self.is_current = is_current
        self.created_at = created_at

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

    def supersede(self) -> None:
        self.is_current = False
