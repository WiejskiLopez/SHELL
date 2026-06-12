"""Application exceptions for shell_ddd."""
from __future__ import annotations


class ApplicationError(Exception):
    """Base class for all domain errors."""


class TemplateGraphNotFoundException(ApplicationError):
    """Raised when task markdown/yaml has invalid structure."""
