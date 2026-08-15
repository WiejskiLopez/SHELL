from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.base.value_object import ValueObject

if TYPE_CHECKING:
    from shell.execution.domain.execution.aggregates.session_execution.value_objects.session_id_ref import (
        SessionIdRef,
    )


@dataclass(frozen=True, slots=True)
class SessionReference(ValueObject):
    """Reference to a session owned by the session BC."""

    session_id: SessionIdRef
