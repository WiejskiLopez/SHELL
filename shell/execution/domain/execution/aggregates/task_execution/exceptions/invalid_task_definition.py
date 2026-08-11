from __future__ import annotations

from shell.platform.domain.exceptions.domain_error import DomainError


class InvalidTaskDefinition(DomainError):
    """Raised when task markdown/yaml has invalid structure."""
