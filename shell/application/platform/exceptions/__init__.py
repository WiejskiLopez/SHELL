"""Application exceptions for shell."""

from __future__ import annotations

from shell.application.definition.exceptions.graph_definition_not_found_exception import (
    GraphDefinitionNotFoundException,
)
from shell.application.platform.exceptions.application_error import ApplicationError

__all__ = [
    "ApplicationError",
    "GraphDefinitionNotFoundException",
]
