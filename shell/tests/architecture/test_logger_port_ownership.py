"""Koncept: jeden kanoniczny port Loggera.

Reguła: Logger należy do application ports, a domena nie definiuje tego
technicznego kontraktu.

Poprawnie: istnieje jedna definicja Logger w application/ports/logger.py,
agregator eksportów nie definiuje drugiej klasy, a domain/ports nie zawiera
Loggera.
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
    domain_logger = ROOT / "platform" / "domain" / "ports" / "log.py"

    assert canonical.exists()
    assert len(_logger_class_definitions(canonical)) == 1
    assert _logger_class_definitions(compatibility) == []
    assert not domain_logger.exists()
