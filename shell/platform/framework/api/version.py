"""API version registry with lifecycle management (RFC 8594).

Definiuje dostępne wersje API, ich status (active/deprecated/sunset)
oraz daty wycofania. Deprecation i Sunset są zwracane jako nagłówki HTTP
zgodnie z RFC 8594 (Sunset header) i RFC 7234 (Deprecation header).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from datetime import date

VersionStatus = Literal["active", "deprecated", "sunset"]


@dataclass(frozen=True)
class ApiVersionInfo:
    version: str
    status: VersionStatus = "active"
    base_path: str = ""
    deprecation_date: date | None = None
    sunset_date: date | None = None


class ApiVersionRegistry:
    """Rejestr wersji API z zarządzaniem cyklem życia.

    active       → pełne wsparcie
    deprecated   → oznaczane nagłówkiem Deprecation
    sunset       → oznaczane nagłówkiem Sunset (wkrótce wycofane)
    """

    def __init__(self, versions: list[ApiVersionInfo]) -> None:
        if not versions:
            raise ValueError("At least one API version must be registered")
        self._versions: dict[str, ApiVersionInfo] = {v.version: v for v in versions}
        self._latest = max(self._versions.keys())

    @property
    def latest(self) -> str:
        return self._latest

    def get_info(self, version: str) -> ApiVersionInfo | None:
        return self._versions.get(version)

    def is_active(self, version: str) -> bool:
        info = self.get_info(version)
        return info is not None and info.status == "active"

    def list_versions(self) -> list[dict[str, object]]:
        return [
            {
                "version": v.version,
                "status": v.status,
                "base_path": v.base_path,
                "deprecation_date": v.deprecation_date.isoformat() if v.deprecation_date else None,
                "sunset_date": v.sunset_date.isoformat() if v.sunset_date else None,
            }
            for v in sorted(self._versions.values(), key=lambda x: x.version, reverse=True)
        ]
