"""Base class for errors raised by application use cases."""

from __future__ import annotations


class ApplicationError(Exception):
    """Base class for errors raised while coordinating an application use case."""
