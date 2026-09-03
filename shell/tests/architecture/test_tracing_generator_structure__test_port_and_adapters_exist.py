"""Koncept: port i adaptery generatora correlation_id.

Reguła: enterprise observability wymaga wymiennego Źródła identyfikatorów
korelacji — port ``CorrelationIdGenerator`` istnieje w „application/context/ports"
i ma implementacje (adaptery) w „infrastructure/identity".

Poprawnie: istnieją port „correlation_id_generator.py" oraz adaptery
„uuid_correlation_id_generator.py" i „static_correlation_id_generator.py".
"""

from __future__ import annotations

import ast

from _arch_helpers import BASE, architecture_assertion_message, parse_file


def test_correlation_id_generator_port_and_adapters_exist() -> None:
    port = BASE / "platform/application/context/ports/correlation_id_generator.py"
    uuid_adapter = BASE / "platform/infrastructure/identity/uuid_correlation_id_generator.py"
    static_adapter = BASE / "platform/infrastructure/identity/static_correlation_id_generator.py"

    violations: list[str] = []
    if not port.exists():
        violations.append(f"Brak portu CorrelationIdGenerator: {port}")
    if not uuid_adapter.exists():
        violations.append(f"Brak adaptera UUID: {uuid_adapter}")
    if not static_adapter.exists():
        violations.append(f"Brak adaptera static: {static_adapter}")

    if port.exists():
        tree = parse_file(port)
        if tree is None:
            violations.append(f"Port nie jest parsowalny: {port}")
        elif not any(
            isinstance(node, ast.ClassDef) and node.name == "CorrelationIdGenerator"
            for node in ast.walk(tree)
        ):
            violations.append(f"Port nie deklaruje klasy CorrelationIdGenerator: {port}")

    assert not violations, architecture_assertion_message(
        "test_correlation_id_generator_port_and_adapters_exist",
        "port CorrelationIdGenerator i adaptery istnieją i są poprawnie nazwane",
        violations,
    )