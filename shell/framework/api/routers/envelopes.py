"""Envelopes router — query envelopes by workflow."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends
from fastapi import Request as _Request

from shell.application.queries.queries import GetEnvelopesByWorkflowQuery

if TYPE_CHECKING:
    from shell.bootstrap.container.core_container import CoreContainer

router = APIRouter(prefix="/envelopes", tags=["envelopes"])


def get_core_container(request: _Request) -> CoreContainer:
    return request.app.state.core_container


@router.get("/workflow/{workflow_id}")
async def list_by_workflow(
    workflow_id: str,
    pending_only: bool = False,
    core_container: CoreContainer = Depends(get_core_container),
) -> dict:  # type: ignore[type-arg]
    result = await core_container.app.buses.query_bus().dispatch(
        GetEnvelopesByWorkflowQuery(workflow_id=workflow_id, pending_only=pending_only)
    )
    envelopes = result if result is not None else []
    return {"workflow_id": workflow_id, "envelopes": [str(e) for e in envelopes]}
