"""Architektura: sprawdza że OutboxEventModel i Envelope.from_message zawsze mają correlation_id.

Reguły:
1. Każde ``OutboxEventModel(...)`` w kodzie produkcyjnym musi zawierać
   ``correlation_id=`` i ``causation_id=`` jako keyword argumenty.
2. Każde ``Envelope.from_message(...)`` w kodzie produkcyjnym musi zawierać
   ``correlation_id=`` jako keyword argument.
"""

from __future__ import annotations

import ast

from _arch_helpers import BASE, iter_py_files, parse_file

_OUTBOX_EVENT_CALLS: set[str] = set()
_ENVELOPE_CALLS: set[str] = set()


def _check_outbox_event_call(node: ast.Call, path: str, line: int) -> str | None:
    if not isinstance(node.func, ast.Name):
        return None
    if node.func.id != "OutboxEventModel":
        return None
    kwargs = {kw.arg for kw in node.keywords if kw.arg is not None}
    missing: list[str] = []
    if "correlation_id" not in kwargs:
        missing.append("correlation_id")
    if "causation_id" not in kwargs:
        missing.append("causation_id")
    if not missing:
        return None
    return f"{path}:{line}: OutboxEventModel() bez {', '.join(missing)}"


def _check_envelope_call(node: ast.Call, path: str, line: int) -> str | None:
    if not isinstance(node.func, ast.Attribute):
        return None
    if node.func.attr != "from_message":
        return None
    # Sprawdź czy to Envelope.from_message (a nie jakiś inny .from_message)
    if not (isinstance(node.func.value, ast.Name) and node.func.value.id == "Envelope"):
        return None
    kwargs = {kw.arg for kw in node.keywords if kw.arg is not None}
    if "correlation_id" in kwargs:
        return None
    return f"{path}:{line}: Envelope.from_message() bez correlation_id"


def test_outbox_event_model_always_has_correlation_and_causation() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE / "shell"):
        tree = parse_file(path)
        if tree is None:
            continue
        rel = path.relative_to(BASE)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                violation = _check_outbox_event_call(node, str(rel), node.lineno)
                if violation:
                    violations.append(violation)
                violation = _check_envelope_call(node, str(rel), node.lineno)
                if violation:
                    violations.append(violation)
    assert not violations, (
        "Wszystkie OutboxEventModel() muszą mieć correlation_id= i causation_id=; "
        "wszystkie Envelope.from_message() muszą mieć correlation_id=:\n" + "\n".join(violations)
    )
