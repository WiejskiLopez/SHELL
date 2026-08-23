"""Koncept: reguła architektoniczna — transport message oparty o ``StateData``.

Reguła: message zawsze przenosi ``state_data`` — w domenie jako ``StateData``,
poza domeną (transport) jako ``JsonStr``. Odbiorcą message może być wyłącznie
agregat posiadający ``_state_data`` — dlatego ``state_data`` NIGDY nie jest
opcjonalny (``None``) ani gołym ``str``.

Poprawnie: ``DomainMessage.state_data`` jest typu ``StateData``, a
``IntegrationMessage.state_data`` — ``JsonStr``; oba są wymagane.
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    parse_file,
)

if TYPE_CHECKING:
    from pathlib import Path


_BASE_FILES = {
    "domain": BASE / "platform" / "domain" / "messages" / "domain_message.py",
    "application": BASE / "platform" / "application" / "messages" / "integration_message.py",
}
_EXPECTED = {
    "domain": ("DomainMessage", "StateData"),
    "application": ("IntegrationMessage", "JsonStr"),
}


def _field_annotation(path: Path, class_name: str, field_name: str) -> str | None:
    tree = parse_file(path)
    if tree is None:
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for stmt in node.body:
                if (
                    isinstance(stmt, ast.AnnAssign)
                    and isinstance(stmt.target, ast.Name)
                    and stmt.target.id == field_name
                    and stmt.annotation is not None
                ):
                    return ast.unparse(stmt.annotation)
    return None


def test_message_state_data_is_typed_and_required() -> None:
    violations: list[str] = []
    for layer, (class_name, expected_type) in _EXPECTED.items():
        annotation = _field_annotation(_BASE_FILES[layer], class_name, "state_data")
        if annotation is None:
            violations.append(
                f"{class_name}.state_data musi być zadeklarowane w bazowym kontrakcie"
            )
            continue
        if expected_type not in annotation:
            violations.append(
                f"{class_name}.state_data musi być typu {expected_type}: {annotation!r}"
            )
    assert not violations, architecture_assertion_message(
        "transport message oparty o StateData",
        "state_data = StateData w domenie, JsonStr w transporcie; wymagane (nigdy None)",
        violations,
    )
