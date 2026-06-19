from __future__ import annotations

from shell.domain.exceptions._base import DomainError


class RunnerConfigNotFound(DomainError):
    def __init__(self, package_name: str) -> None:
        super().__init__(f"RunnerConfig not found: {package_name!r}")
