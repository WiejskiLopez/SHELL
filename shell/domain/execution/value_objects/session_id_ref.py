from __future__ import annotations

from shell.domain.platform.base.entity_id import EntityId


class SessionIdRef(EntityId):
    """Execution BC's reference to a Session from session BC.

    Intentionally duplicated for BC isolation.
    See shell.domain.session.aggregates.session.value_objects.session_id.SessionId
    """

    pass
