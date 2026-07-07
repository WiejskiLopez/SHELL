"""Re-exports for User BC mappers — kept for backward compatibility."""

from __future__ import annotations

from shell.infrastructure.user.user.persistence.sql.mappers import (
    user_entity_to_model,
    user_model_to_entity,
    user_update_model,
)
from shell.infrastructure.user.user_skill.persistence.sql.mappers import (
    user_skill_entity_to_model,
    user_skill_model_to_entity,
)
from shell.infrastructure.user.user_state.persistence.sql.mappers import (
    user_state_entity_to_model,
    user_state_model_to_entity,
)

__all__ = [
    "user_entity_to_model",
    "user_model_to_entity",
    "user_skill_entity_to_model",
    "user_skill_model_to_entity",
    "user_state_entity_to_model",
    "user_state_model_to_entity",
    "user_update_model",
]
