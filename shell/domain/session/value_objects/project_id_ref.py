from __future__ import annotations

from shell.domain.platform.base.entity_id import EntityId


class ProjectIdRef(EntityId):
    """Session BC's reference to a Project from projekt BC.

    Intentionally duplicated for BC isolation.
    See shell.domain.projekt.value_objects.project_id.ProjectId
    """

    pass
