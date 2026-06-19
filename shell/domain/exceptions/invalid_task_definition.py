from __future__ import annotations

from shell.domain.exceptions._base import DomainError


class InvalidTaskDefinition(DomainError):
    """Raised when task markdown/yaml has invalid structure."""
