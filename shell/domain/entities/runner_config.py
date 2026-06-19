"""RunnerConfig aggregate — serialized runner/module configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.entities.base.entity import Entity

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.value_objects.hash import Hash
    from shell.domain.value_objects.ids import RunnerConfigId


class RunnerConfig(Entity[RunnerConfigId]):
    __slots__ = ("package_name", "kind", "hash", "body", "created_at")

    def __init__(
        self,
        id: RunnerConfigId,
        package_name: str,
        kind: str,
        hash: Hash,
        body: dict[str, object],
        created_at: datetime,
    ) -> None:
        super().__init__(id)
        self.package_name = package_name
        self.kind = kind
        self.hash = hash
        self.body = body
        self.created_at = created_at

    @classmethod
    def new(
        cls,
        *,
        id_: RunnerConfigId,
        package_name: str,
        kind: str,
        body: dict[str, object],
        config_hash: Hash,
        now: datetime,
    ) -> RunnerConfig:
        return cls(
            id=id_,
            package_name=package_name,
            kind=kind,
            hash=config_hash,
            body=body,
            created_at=now,
        )
