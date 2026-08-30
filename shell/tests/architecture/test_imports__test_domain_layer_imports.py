"""Koncept: reguła architektoniczna dotycząca imports: test domain layer imports.

Reguła: test sprawdza kontrakt architektoniczny imports: test domain layer imports.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    get_imports,
    iter_domain_files,
)

_FORBIDDEN_LAYERS: frozenset[str] = frozenset(
    {
        "application",
        "process",
        "infrastructure",
        "framework",
        "bootstrap",
    }
)
_FORBIDDEN_EXTERNAL: frozenset[str] = frozenset({"sqlalchemy", "pydantic", "fastapi", "motor"})


def _is_forbidden_domain_import(imp: str) -> bool:
    """Domain files may only reach platform/domain + own domain. Flag any
    cross-layer shell import (any bounded context) plus web/ORM frameworks."""
    if any(imp == prefix or imp.startswith(prefix + ".") for prefix in _FORBIDDEN_EXTERNAL):
        return True
    parts = imp.split(".")
    # shell.<owner>.<layer> — layer is always the third segment, whether the
    # owner is `platform` or a bounded context (e.g. execution_service).
    return len(parts) >= 3 and parts[0] == "shell" and parts[2] in _FORBIDDEN_LAYERS


def test_domain_layer_imports() -> None:
    violations: list[str] = []
    for path in iter_domain_files():
        for imp in get_imports(path):
            if not _is_forbidden_domain_import(imp):
                continue
            rel = path.relative_to(BASE).as_posix()
            violations.append(f"{rel}: imports {imp!r}")
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_domain_layer_imports",
        "warunek zapisany w asercji musi być spełniony",
        "Domain layer import violations:\n" + "\n".join(violations),
    )
