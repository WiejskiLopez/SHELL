"""Application exceptions for shell."""

from __future__ import annotations

from shell.application.platform.exceptions.application_error import ApplicationError
from shell.application.definition.exceptions.graph_definition_not_found_exception import GraphDefinitionNotFoundException

__all__ = [
    "ApplicationError",
    "GraphDefinitionNotFoundException",
]
