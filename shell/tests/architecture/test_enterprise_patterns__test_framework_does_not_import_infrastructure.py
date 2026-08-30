"""Koncept: reguła architektoniczna dotycząca enterprise patterns: test framework does not import infrastructure.

Reguła: test sprawdza kontrakt architektoniczny enterprise patterns: test framework does not import infrastructure.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    get_imports,
    iter_layer_files,
)


def test_framework_does_not_import_infrastructure() -> None:
    violations: list[str] = []
    for path in iter_layer_files("framework"):
        rel = path.relative_to(BASE).as_posix()
        for imp in get_imports(path):
            parts = imp.split(".")
            if len(parts) >= 3 and parts[0] == "shell" and parts[2] == "infrastructure":
                violations.append(f"{rel}: imports {imp!r}")
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_framework_does_not_import_infrastructure",
        "warunek zapisany w asercji musi być spełniony",
        "framework/ must not import from infrastructure/:\n" + "\n".join(violations),
    )
