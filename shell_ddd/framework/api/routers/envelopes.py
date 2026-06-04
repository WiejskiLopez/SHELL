"""Envelopes router — query envelopes by workflow."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from shell_ddd.application.queries.queries import GetEnvelopesByWorkflowQuery
from shell_ddd.bootstrap.container import Container

router = APIRouter(prefix="/envelopes", tags=["envelopes"])


from fastapi import Request as _Request


def get_container(request: _Request) -> Container:
    return request.app.state.container


@router.get("/workflow/{workflow_id}")
async def list_by_workflow(
    workflow_id: str,
    pending_only: bool = False,
    container: Container = Depends(get_container),
) -> dict:  # type: ignore[type-arg]
    result = await container.query_bus.dispatch(
        GetEnvelopesByWorkflowQuery(workflow_id=workflow_id, pending_only=pending_only)
    )
    envelopes = result if result is not None else []
    return {"workflow_id": workflow_id, "envelopes": [str(e) for e in envelopes]}
