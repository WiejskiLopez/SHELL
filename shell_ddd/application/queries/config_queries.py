from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetRunnerConfigQuery:
    package_name: str
