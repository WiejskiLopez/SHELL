from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.session_service.domain.session.aggregates.session_state.session_state import (
        SessionState,
    )
    from shell.session_service.infrastructure.session.session_state.persistence.sql.models.session_state import (
        SessionStateModel,
    )


def session_state_change_model(model: SessionStateModel, entity: SessionState) -> None:
    model.session_id = entity.session_id.value
    model.direction = entity.direction.value
    model.state_data = json.loads(entity.state_data.value.value)
    model.deleted_at = entity._deleted_at.value
