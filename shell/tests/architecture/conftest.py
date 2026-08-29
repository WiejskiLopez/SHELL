from __future__ import annotations

import pathlib
import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from wheel_helpers import ServiceWheels

THIS_DIR = pathlib.Path(__file__).resolve().parent

if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))


@pytest.fixture(scope="session")
def artifact_services(tmp_path_factory: pytest.TempPathFactory) -> dict[str, ServiceWheels]:
    """Build every wheel once per session and share them across the isolation tests.

    Enterprise rule: artifacts are built once and consumed, never rebuilt in
    every test. Without this cache the artifact-isolation tests triggered ~30
    ``uv build`` runs per execution (~110 s); with it the whole set is built a
    single time per session.
    """
    from wheel_helpers import build_service_wheels

    return build_service_wheels(tmp_path_factory.mktemp("artifact-wheels"))
