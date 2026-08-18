from __future__ import annotations

from fastapi import FastAPI

from shell.platform.framework.api.openapi import configure_openapi


def test_configure_openapi_uses_caller_owned_metadata() -> None:
    app = FastAPI()

    configure_openapi(
        app,
        title="Example API",
        version="1.2.3",
        description="Example service.",
        tags=({"name": "Example", "description": "Example endpoints."},),
    )

    assert app.title == "Example API"
    assert app.version == "1.2.3"
    assert app.description == "Example service."
    assert app.openapi_tags == [{"name": "Example", "description": "Example endpoints."}]


def test_configure_openapi_has_no_platform_tag_defaults() -> None:
    app = FastAPI()

    configure_openapi(app)

    assert app.openapi_tags == []
