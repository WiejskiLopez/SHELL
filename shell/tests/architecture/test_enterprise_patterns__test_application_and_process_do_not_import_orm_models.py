"""Koncept: reguła architektoniczna dotycząca enterprise patterns: test application and process do not import orm models.

Reguła: test sprawdza kontrakt architektoniczny enterprise patterns: test application and process do not import orm models.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    get_imports,
    iter_layer_files,
)


def test_application_and_process_do_not_import_orm_models() -> None:
    violations: list[str] = []
    for layer in ["application"]:
        for path in iter_layer_files(layer):
            rel = path.relative_to(BASE).as_posix()
            for imp in get_imports(path):
                parts = imp.split(".")
                if (
                    len(parts) >= 3
                    and parts[0] == "shell"
                    and parts[2] == "infrastructure"
                    and "model" in imp.lower()
                ):
                    violations.append(f"{rel}: imports infrastructure model {imp!r}")
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_application_and_process_do_not_import_orm_models",
        "warunek zapisany w asercji musi być spełniony",
        "Application layer must not import ORM models directly:\n" + "\n".join(violations),
    )
