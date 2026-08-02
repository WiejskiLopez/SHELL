"""Central message registry for outbox/inbox deserialization.

Auto-generated. Run .opencode/tools/regenerate_registry.py to rebuild.
"""

from __future__ import annotations

from shell.domain.messaging.aggregates.message_router.messages.routable_message import (
    RoutableMessage,
)


def build_message_registry() -> dict[str, type]:
    """Build registry mapping class names to message types for deserialization."""
    messages: list[type] = [
        RoutableMessage,
    ]

    return {message.__name__: message for message in messages}
