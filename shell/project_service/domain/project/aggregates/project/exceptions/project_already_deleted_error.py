from __future__ import annotations

from shell.platform.domain.exceptions.domain_error import DomainError


class ProjectAlreadyDeletedError(DomainError):
    pass