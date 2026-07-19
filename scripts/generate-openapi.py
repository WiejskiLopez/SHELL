#!/usr/bin/env python
"""Generates openapi.json from the FastAPI application."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from shell.platform.framework.api.app import create_monolith_app


def main() -> None:
    app = create_monolith_app(core_container=MagicMock())
    with open("openapi.json", "w") as f:
        json.dump(app.openapi(), f, indent=2)
    print("OK: openapi.json generated")


if __name__ == "__main__":
    main()
