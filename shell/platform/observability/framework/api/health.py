"""Health routing helpers — attach readiness to any BC FastAPI app."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.observability.framework.api.providers import ObservabilityProviders
from shell.platform.observability.framework.api.readiness import create_readiness_router

if TYPE_CHECKING:
    from fastapi import FastAPI


def mount_readiness(app: FastAPI, providers: ObservabilityProviders) -> None:
    """Mount ``GET /readiness``.

    ``/health`` remains the liveness signal defined by each BC app; ``/readiness``
    reflects real readiness (DB, migrations, worker activity, broker, backlog).
    Błąd providu jest twardy (AttributeError przy braku ``readiness_probe``) —
    serwis z czytą deklaracją obserwowalności nie może cicho zgubić endpointu.
    """
    app.include_router(create_readiness_router(providers.readiness_probe()))
