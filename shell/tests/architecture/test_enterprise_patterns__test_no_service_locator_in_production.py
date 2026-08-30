"""Koncept: reguła architektoniczna dotycząca enterprise patterns: test no service locator in production.

Reguła: test sprawdza kontrakt architektoniczny enterprise patterns: test no service locator in production.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    get_imports,
    iter_layer_files,
)

_SERVICE_LOCATOR_PATTERNS: frozenset[str] = frozenset(
    {"dependency_injector.providers", "dependency_injector.containers"}
)


def test_no_service_locator_in_production() -> None:
    violations: list[str] = []
    for layer in ["application", "infrastructure", "framework"]:
        for path in iter_layer_files(layer):
            rel = path.relative_to(BASE).as_posix()
            for imp in get_imports(path):
                if imp in _SERVICE_LOCATOR_PATTERNS or "dependency_injector" in imp:
                    violations.append(f"{rel}: uses {imp!r}")
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_no_service_locator_in_production",
        "warunek zapisany w asercji musi być spełniony",
        "Service Locator (dependency_injector) must not be used outside bootstrap/:\n"
        + "\n".join(violations),
    )
