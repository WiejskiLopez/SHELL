"""Resolves annotation types for payload (de)serialization.

Annotations are strings (``from __future__ import annotations``), and domaitypes (ValueObjects, JsonStr, plain dataclasses) are reachable through the
loaded modules.  This resolver builds a namespace from the class MRO module
globals plus known platform types, fills any remaining name by scanning the
loaded modules, and returns the fully resolved hints.  A hint that cannot be
resolved raises instead of silently degrading to a raw passthrough.
"""

from __future__ import annotations

import re
import sys
from datetime import datetime
from typing import get_type_hints

from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.infrastructure.serialization.errors import UnresolvableTypeHintError
from shell.platform.types import JsonStr

_PLATFORM_TYPES: dict[str, object] = {
    "CreatedAt": CreatedAt,
    "OccurredAt": OccurredAt,
    "JsonStr": JsonStr,
    "datetime": datetime,
}


class PayloadTypeHintsResolver:
    """Resolves annotation maps used by payload serializers and deserializers."""

    def __init__(self) -> None:
        self._cache: dict[type, dict[str, object]] = {}
        self._name_cache: dict[str, type | None] = {}

    def resolve(self, target_cls: type) -> dict[str, object]:
        cached = self._cache.get(target_cls)
        if cached is not None:
            return cached
        namespace = self._build_namespace(target_cls)
        try:
            hints = get_type_hints(target_cls, globalns=namespace, localns=namespace)
        except (NameError, TypeError) as exc:
            raise UnresolvableTypeHintError(
                f"cannot resolve type hints for {target_cls.__name__}: {exc}"
            ) from exc
        self._cache[target_cls] = hints
        return hints

    def _build_namespace(self, target_cls: type) -> dict[str, object]:
        namespace: dict[str, object] = {}
        for base in target_cls.__mro__:
            module = sys.modules.get(base.__module__)
            if module is not None:
                namespace.update(vars(module))
        namespace.update(_PLATFORM_TYPES)
        for name in _annotation_names(target_cls):
            if name in namespace:
                continue
            resolved = self._find_in_modules(name)
            if resolved is not None:
                namespace[name] = resolved
        return namespace

    def _find_in_modules(self, name: str) -> type | None:
        cached = self._name_cache.get(name)
        if cached is not None or name in self._name_cache:
            return cached
        for module in list(sys.modules.values()):
            candidate = getattr(module, name, None)
            if isinstance(candidate, type):
                self._name_cache[name] = candidate
                return candidate
        self._name_cache[name] = None
        return None


def _annotation_names(target_cls: type) -> set[str]:
    names: set[str] = set()
    for base in target_cls.__mro__:
        for annotation in getattr(base, "__annotations__", {}).values():
            if isinstance(annotation, str):
                names.update(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", annotation))
    return names
