"""RunnerConfig entity — serialized runner/module configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.value_objects.ids import RunnerConfigId
from shell.domain.platform.base.entity import Entity

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.platform.value_objects.hash import Hash


class RunnerConfig(Entity[RunnerConfigId]):
    __slots__ = ("_package_name", "_kind", "_hash", "_body", "_created_at")

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
        self._package_name = package_name
        self._kind = kind
        self._hash = hash
        self._body = body
        self._created_at = created_at

    @property
    def package_name(self) -> str:
        return self._package_name

    @property
    def kind(self) -> str:
        return self._kind

    @property
    def hash(self) -> Hash:
        return self._hash

    @property
    def body(self) -> dict[str, object]:
        return self._body

    @property
    def created_at(self) -> datetime:
        return self._created_at

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
