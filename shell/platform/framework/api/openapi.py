from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from fastapi import FastAPI


def configure_openapi(
    app: FastAPI,
    *,
    title: str | None = None,
    version: str | None = None,
    description: str | None = None,
    tags: Sequence[Mapping[str, str]] | None = None,
) -> None:
    """Apply caller-owned OpenAPI metadata without service knowledge."""
    if title is not None:
        app.title = title
    if version is not None:
        app.version = version
    if description is not None:
        app.description = description
    app.openapi_tags = [dict(tag) for tag in tags or ()]
