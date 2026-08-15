"""Health routing helpers — attach readiness to any BC FastAPI app."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.platform.framework.api.readiness import create_readiness_router

if TYPE_CHECKING:
    from fastapi import FastAPI

    from shell.platform.framework.api.dependencies import ContainerProtocol


def mount_readiness(app: FastAPI, core_container: ContainerProtocol | Any) -> None:
    """Mount ``GET /readiness`` when the container exposes a readiness probe.

    ``/health`` remains the liveness signal defined by each BC app; ``/readiness``
    is added only when a ``readiness_probe`` provider is registered on the
    container, so BCs without delivery workers stay liveness-only.
    """
    readiness_probe = getattr(core_container, "readiness_probe", None)
    if readiness_probe is not None:
        app.include_router(create_readiness_router(readiness_probe()))
