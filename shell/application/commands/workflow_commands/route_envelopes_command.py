from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RouteEnvelopesCommand:
    workflow_id: str
