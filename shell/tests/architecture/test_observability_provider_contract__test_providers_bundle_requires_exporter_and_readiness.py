"""Koncept: jawny bundle providów wymaga kluczowych pól.

Reguła: `ObservabilityProviders` musi deklarować wymagane providy
`metrics_exporter` i `readiness_probe` jako jawnie przypisane pola, żeby brak
providu w kontenerze był twardym błędem w `from_container`, a nie cichym
pominięciem endpointu.

Poprawnie: bundle ma pola metryk i readiness z adnotacjami typu.
"""

from __future__ import annotations

import ast

from _arch_helpers import BASE, parse_file

_PROVIDERS = BASE / "platform" / "observability" / "framework" / "api" / "providers.py"


def test_providers_bundle_requires_exporter_and_readiness() -> None:
    tree = parse_file(_PROVIDERS)
    assert tree is not None, "providers.py nie sparsowano"
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "ObservabilityProviders":
            assigned = {
                stmt.target.id
                for stmt in node.body
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)
            }
            missing = {"metrics_exporter", "readiness_probe"} - assigned
            assert not missing, f"ObservabilityProviders musi wymagać: {sorted(missing)}"
            return
    raise AssertionError("ObservabilityProviders nie znaleziono w providers.py")
