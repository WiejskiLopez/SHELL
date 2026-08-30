"""Koncept: reguła architektoniczna dotycząca regressions: test versioned models wire version_id_col.

Reguła: test sprawdza kontrakt architektoniczny regressions: test versioned models wire version_id_col.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    iter_layer_files,
)


def test_every_versioned_model_wires_version_id_col() -> None:
    violations: list[str] = []
    for path in iter_layer_files("infrastructure"):
        if "models" not in path.parts or path.name == "__init__.py":
            continue
        src = path.read_text(encoding="utf-8")
        # Pomija re-exporty i mixin: pilnujemy modeli, które dziedziczą VersionedMixin
        if "VersionedMixin" not in src:
            continue
        if path.name == "versioned.py" or "mixins" in path.parts:
            continue
        if "version_id_col" not in src:
            rel = path.relative_to(BASE).as_posix()
            violations.append(
                f"{rel}: dziedziczy VersionedMixin, ale nie podpięto version_id_col w __mapper_args__"
            )
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_every_versioned_model_wires_version_id_col",
        "warunek zapisany w asercji musi być spełniony",
        "VersionedMixin wymaga `__mapper_args__` z `version_id_col` — inaczej lok jest iluzoryczny:\n"
        + "\n".join(violations),
    )
