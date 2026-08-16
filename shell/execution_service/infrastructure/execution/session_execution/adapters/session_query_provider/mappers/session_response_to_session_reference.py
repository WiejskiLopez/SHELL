from __future__ import annotations

from typing import TYPE_CHECKING

from shell.execution_service.domain.execution.aggregates.session_execution.value_objects.session_id_ref import (
    SessionIdRef,
)
from shell.execution_service.domain.execution.aggregates.session_execution.value_objects.session_reference import (
    SessionReference,
)

if TYPE_CHECKING:
    from shell.execution_service.infrastructure.execution.session_execution.adapters.session_query_provider.contracts.v1.session_response import (
        SessionResponseV1,
    )


def session_response_to_session_reference(
    response: SessionResponseV1,
) -> SessionReference:
    return SessionReference(session_id=SessionIdRef(response.id))
