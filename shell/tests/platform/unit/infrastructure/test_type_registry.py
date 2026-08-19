from __future__ import annotations

import pytest

from shell.platform.infrastructure.serialization.registries.type_registry import build_type_registry


def test_type_registry_rejects_duplicate_class_names() -> None:
    first = type("DuplicateEvent", (), {})
    second = type("DuplicateEvent", (), {})

    with pytest.raises(ValueError, match="Duplicate registry key: DuplicateEvent"):
        build_type_registry((first, second))


def test_type_registry_accepts_the_same_class_more_than_once() -> None:
    event_type = type("StableEvent", (), {})

    assert build_type_registry((event_type, event_type)) == {"StableEvent": event_type}
