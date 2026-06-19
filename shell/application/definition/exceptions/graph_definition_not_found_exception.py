"""Raised when task markdown/yaml has invalid structure."""

from __future__ import annotations

from shell.application.platform.exceptions.application_error import ApplicationError


class GraphDefinitionNotFoundException(ApplicationError):
    """Raised when task markdown/yaml has invalid structure."""
