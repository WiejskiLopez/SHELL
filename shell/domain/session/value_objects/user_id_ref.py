from __future__ import annotations

from shell.platform.domain.base.entity_id import EntityId


class UserIdRef(EntityId):
    """Session BC's reference to a User from user BC.

    Intentionally duplicated for BC isolation.
    See shell.domain.user.value_objects.user_id.UserId
    """

    pass
