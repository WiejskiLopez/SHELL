from __future__ import annotations


def source_service_for_type(object_type: type[object]) -> str:
    parts = object_type.__module__.split(".")
    if len(parts) < 2 or parts[0] != "shell" or not parts[1].endswith("_service"):
        raise ValueError(f"Cannot derive source service from {object_type.__module__}")
    return parts[1]
