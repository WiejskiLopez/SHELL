"""Subscribe event handlers to EventBus.

Cross-BC communication uses source-owned integration events:
each BC defines integration events in its own application layer
(``application/<bc>/<aggregate>/integration_events/``).

The composition root imports from the source BC — this is the only
cross-BC import, and it imports an integration event, not a domain type.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.platform.bootstrap.container.core_container import CoreContainer


def register_events(_core_container: CoreContainer) -> None:
    """Register cross-context event subscriptions."""

