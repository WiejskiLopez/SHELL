"""PayloadUpcaster — schema version migration for delivery payloads.

A consumer supports the current and the previous payload versions (ref2.md
§4.3). An upcaster transforms a payload of version N into version N+1, so the
deserializer can always build the current aggregate/event shape regardless of
the version stored in the envelope. Unknown (too new) versions are rejected by
the envelope validator before they reach the upcaster.

The registry maps ``type -> {source_version: transform(payload) -> payload}``.
``upcast`` applies the chain N -> N+1 -> ... until no transform is registered.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping

PayloadTransform = Callable[[dict[str, object]], dict[str, object]]


class PayloadUpcaster:
    def __init__(
        self,
        transforms: Mapping[str, Mapping[int, PayloadTransform]] | None = None,
    ) -> None:
        self._transforms: dict[str, dict[int, PayloadTransform]] = {
            type_name: dict(versions) for type_name, versions in (transforms or {}).items()
        }

    def upcast(
        self,
        type_name: str,
        schema_version: int,
        payload: dict[str, object],
    ) -> tuple[dict[str, object], int]:
        """Return the upcast payload and its final schema version."""
        current = payload
        version = schema_version
        versions = self._transforms.get(type_name, {})
        while version in versions:
            current = versions[version](current)
            version += 1
        return current, version

    def has_upcaster(self, type_name: str) -> bool:
        return type_name in self._transforms
