"""Koncept: jeden kanoniczny kontrakt application ports.

Reguła: porty aplikacyjne są importowane z konkretnych modułów, a domena nie
definiuje technicznych kontraktów obserwowalności.

Poprawnie: istnieje jedna definicja Logger w application/ports/logger.py,
agregatory application/ports nie istnieją, a domain/ports nie zawiera Loggera.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _logger_class_definitions(path: Path) -> list[ast.ClassDef]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        node for node in ast.walk(tree) if isinstance(node, ast.ClassDef) and node.name == "Logger"
    ]


def test_logger_port_has_one_application_owner() -> None:
    canonical = ROOT / "platform" / "application" / "ports" / "logger.py"
    compatibility = ROOT / "platform" / "application" / "ports" / "ports.py"
    identity_compatibility = ROOT / "platform" / "application" / "ports" / "identity.py"
    domain_logger = ROOT / "platform" / "domain" / "ports" / "log.py"

    assert canonical.exists()
    assert len(_logger_class_definitions(canonical)) == 1
    assert not compatibility.exists()
    assert not identity_compatibility.exists()
    assert not domain_logger.exists()

    old_imports = ("application.ports." + "ports", "application.ports." + "identity")
    for source in ROOT.rglob("*.py"):
        content = source.read_text(encoding="utf-8")
        assert not any(old_import in content for old_import in old_imports), source
