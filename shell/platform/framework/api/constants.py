"""API versioning constants — wygenerowane z ApiVersionRegistry."""

from __future__ import annotations

from shell.platform.framework.api.version import ApiVersionInfo, ApiVersionRegistry

API_VERSION_REGISTRY: ApiVersionRegistry = ApiVersionRegistry(
    [
        ApiVersionInfo(version="v1", status="active", base_path="/api/v1"),
    ]
)

API_PREFIX = API_VERSION_REGISTRY.get_info("v1").base_path  # type: ignore[union-attr]
API_LATEST_VERSION = API_VERSION_REGISTRY.latest
