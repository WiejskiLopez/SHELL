"""Application exceptions for shell."""
from __future__ import annotations


class ApplicationError(Exception):
    """Base class for all domain errors."""


class TemplateGraphNotFoundException(ApplicationError):
    """Raised when task markdown/yaml has invalid structure."""
