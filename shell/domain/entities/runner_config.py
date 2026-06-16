"""RunnerConfig aggregate — serialized runner/module configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.value_objects.hash import Hash
    from shell.domain.value_objects.ids import RunnerConfigId


@dataclass(slots=True)
class RunnerConfig:
    id: RunnerConfigId
    package_name: str
    kind: str
    hash: Hash
    body: dict[str, object]
    created_at: datetime

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
