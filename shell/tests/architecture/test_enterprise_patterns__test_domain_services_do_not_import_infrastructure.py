"""Koncept: reguła architektoniczna dotycząca enterprise patterns: test domain services do not import infrastructure.

Reguła: test sprawdza kontrakt architektoniczny enterprise patterns: test domain services do not import infrastructure.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    get_imports,
    iter_named_dirs,
    iter_py_files,
)


def test_domain_services_do_not_import_infrastructure() -> None:
    violations: list[str] = []
    for services_dir in iter_named_dirs("domain", "services"):
        for py_file in iter_py_files(services_dir):
            for imp in get_imports(py_file):
                parts = imp.split(".")
                if len(parts) >= 3 and parts[0] == "shell" and parts[2] == "infrastructure":
                    violations.append(f"{py_file.relative_to(BASE)}: imports {imp!r}")
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_domain_services_do_not_import_infrastructure",
        "warunek zapisany w asercji musi być spełniony",
        "Domain services must not import from infrastructure/:\n" + "\n".join(violations),
    )
