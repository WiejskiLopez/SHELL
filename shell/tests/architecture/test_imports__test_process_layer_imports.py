"""Koncept: reguła architektoniczna dotycząca imports: test process layer imports.

Reguła: test sprawdza kontrakt architektoniczny imports: test process layer imports.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    get_imports,
    iter_layer_files,
)

_FORBIDDEN_LAYERS: frozenset[str] = frozenset(
    {"process", "infrastructure", "framework", "bootstrap"}
)
_FORBIDDEN_EXTERNAL: frozenset[str] = frozenset({"sqlalchemy", "fastapi", "motor"})


def _is_forbidden_process_import(imp: str) -> bool:
    """Process/application-handler code may only reach domain (and the
    application layer). Flag any cross-layer shell import plus web/ORM frameworks."""
    if any(imp == prefix or imp.startswith(prefix + ".") for prefix in _FORBIDDEN_EXTERNAL):
        return True
    parts = imp.split(".")
    return len(parts) >= 3 and parts[0] == "shell" and parts[2] in _FORBIDDEN_LAYERS


def test_process_layer_imports() -> None:
    violations: list[str] = []
    for path in iter_layer_files("process"):
        for imp in get_imports(path):
            if not _is_forbidden_process_import(imp):
                continue
            rel = path.relative_to(BASE).as_posix()
            violations.append(f"{rel}: imports {imp!r}")
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_process_layer_imports",
        "warunek zapisany w asercji musi być spełniony",
        "Process layer import violations:\n" + "\n".join(violations),
    )
