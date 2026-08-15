from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetRunnerConfigByIdQuery:
    runner_config_id: str
