"""Envelopes router — query envelopes by workflow."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends
from fastapi import Request as _Request
from shell.application.platform.queries.queries import GetEnvelopesByWorkflowQuery

if TYPE_CHECKING:
    from shell.application.platform.bus.query_bus import QueryBus
    from shell.bootstrap.platform.container.core_container import CoreContainer
    # Dopasuj ścieżkę importu QueryBus do struktury swojego projektu:

router = APIRouter(prefix="/envelopes", tags=["envelopes"])


# ------------------------------------------------------------------
# FastAPI Dependencies (Inversion of Control)
# ------------------------------------------------------------------


def get_core_container(request: _Request) -> CoreContainer:
    return request.app.state.core_container


def get_query_bus(container: CoreContainer = Depends(get_core_container)) -> QueryBus:
    """Ekstrahuje QueryBus i izoluje dynamiczne typowanie na granicy infrastruktury."""
    return container.app.buses.query_bus()  # type: ignore[attr-defined]


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------


@router.get("/workflow/{workflow_id}")
async def list_by_workflow(
    workflow_id: str,
    pending_only: bool = False,
    query_bus: QueryBus = Depends(get_query_bus),  # Wstrzyknięty czysty konkret
) -> dict:
    result = await query_bus.dispatch(
        GetEnvelopesByWorkflowQuery(workflow_id=workflow_id, pending_only=pending_only)
    )
    envelopes = result if result is not None else []
    return {"workflow_id": workflow_id, "envelopes": [str(envelope) for envelope in envelopes]}
