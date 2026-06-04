"""RunnerConfig aggregate — serialized runner/module configuration."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell_ddd.domain.value_objects.hash import Hash

if TYPE_CHECKING:
    from shell_ddd.domain.value_objects.ids import RunnerConfigId


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
        now: datetime | None = None,
    ) -> RunnerConfig:
        import json

        serialized = json.dumps(body, sort_keys=True)
        return cls(
            id=id_,
            package_name=package_name,
            kind=kind,
            hash=Hash.of(serialized),
            body=body,
            created_at=now or datetime.now(tz=UTC),
        )
