"""Exceptions for the domain→integration event mapping layer."""

from __future__ import annotations


class IntegrationMappingError(ValueError):
    """A domain event has no corresponding integration event contract.

    Raised when an aggregate emits a domain event that the bounded context
    intends to publish cross-BC, but no ``*IntegrationEvent`` type exists for it.

    This is a programming/config error, not a runtime business error: the fix is
    to declare the missing integration event (or explicitly mark the domain
    event as internal-only and out of scope for outbox publishing).

    Inherits from :class:`ValueError` so existing ``except ValueError``
    consumers keep working.
    """
