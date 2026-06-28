"""RunnerConfig entity — serialized runner/module configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.value_objects.created_at import CreatedAt
from shell.domain.definition.value_objects.ids import RunnerConfigId
from shell.domain.definition.value_objects.package_name import PackageName
from shell.domain.definition.value_objects.runner_body import RunnerBody
from shell.domain.definition.value_objects.runner_kind import RunnerKind
from shell.domain.platform.base.entity import Entity

if TYPE_CHECKING:
    from shell.domain.platform.value_objects.hash import Hash


class RunnerConfig(Entity[RunnerConfigId]):
    __slots__ = ("_package_name", "_kind", "_hash", "_body", "_created_at")

    def __init__(
        self,
        id: RunnerConfigId,
        package_name: PackageName,
        kind: RunnerKind,
        hash: Hash,
        body: RunnerBody,
        created_at: CreatedAt,
    ) -> None:
        super().__init__(id)
        self._package_name = package_name if isinstance(package_name, PackageName) else PackageName(package_name)
        self._kind = kind if isinstance(kind, RunnerKind) else RunnerKind(kind)
        self._hash = hash
        self._body = body if isinstance(body, RunnerBody) else RunnerBody(body)
        self._created_at = created_at if isinstance(created_at, CreatedAt) else CreatedAt(created_at)

    @property
    def package_name(self) -> PackageName:
        return self._package_name

    @property
    def kind(self) -> RunnerKind:
        return self._kind

    @property
    def hash(self) -> Hash:
        return self._hash

    @property
    def body(self) -> RunnerBody:
        return self._body

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @classmethod
    def new(
        cls,
        *,
        id_: RunnerConfigId,
        package_name: PackageName,
        kind: RunnerKind,
        body: RunnerBody,
        config_hash: Hash,
        now: CreatedAt,
    ) -> RunnerConfig:
        return cls(
            id=id_,
            package_name=package_name,
            kind=kind,
            hash=config_hash,
            body=body,
            created_at=now,
        )
