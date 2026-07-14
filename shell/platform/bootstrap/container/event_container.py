"""Lightweight event sub-container declaration for ``ApplicationContainer`` DI wiring.

This container ONLY declares dependencies (``infra``, ``domain``, ``buses``)
without registering any providers.  It exists so ``ApplicationContainer``
can wire the event sub-graph before the actual providers are resolved
by ``CoreContainer`` via ``EventsContainer``.

See ``events_container.py`` for the full provider implementation.
"""

from __future__ import annotations

from dependency_injector import containers, providers


class EventContainer(containers.DeclarativeContainer):
    """Declares event sub-container dependencies for DI wiring."""

    infra = providers.DependenciesContainer()
    domain = providers.DependenciesContainer()
    buses = providers.DependenciesContainer()
