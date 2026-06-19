from __future__ import annotations

from typing import Protocol

from shell.application.dto import EnvelopeDto


class EnvelopeQueryService(Protocol):
    """Port do listowania kopert (np. dla routera)."""

    async def get_envelopes_by_workflow(
        self, workflow_id: str, pending_only: bool = False
    ) -> list[EnvelopeDto]: ...
