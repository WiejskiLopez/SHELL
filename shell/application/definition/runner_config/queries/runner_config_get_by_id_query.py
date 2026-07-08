from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RunnerConfigGetByIdQuery:
    runner_config_id: str
