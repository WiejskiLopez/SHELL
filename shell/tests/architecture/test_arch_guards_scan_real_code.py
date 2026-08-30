"""Koncept: własność samokontroli suite testów architektury — strażnik strażników.

Reguła: każdy test architektury/izolacji musi faktycznie skanować realny kod. Żaden test nie może
iterować po nieistniejących ścieżkach warstwy (np. `BASE/"application"`, `BASE/"process"` po
migracji na per-BC), bo wtedy przechodzi zawsze i nie chroni przed regresjami. Współdzielone
iteratory `_arch_helpers` muszą zwracać niepuste zbiory plików dla warstw i katalogów, z których
korzysta suite.

Poprawnie: każdy plik testu architektury unika dosłownych ścieżek `BASE/<warstwa>` nad które nie
istnieją jako nadrzędny katalog; iteratory `_arch_helpers` zwracają realne pliki.
"""

from __future__ import annotations

import re

from _arch_helpers import (
    BASE,
    SERVICE_ROOTS,
    architecture_assertion_message,
    iter_domain_files,
    iter_layer_files,
    iter_named_dirs,
    iter_py_files,
)

_LAYER_NAMES = ("application", "domain", "framework", "infrastructure", "bootstrap", "process")
_TECHNICAL_MODULES = frozenset({"conftest.py", "_arch_helpers.py", "__init__.py"})


def _assert_iterators_non_empty() -> list[str]:
    """Every shared iterator must yield at least one real file/directory."""
    problems: list[str] = []
    for layer in ("domain", "application", "framework", "infrastructure"):
        count = len(list(iter_layer_files(layer)))
        if count == 0:
            problems.append(f"iter_layer_files({layer!r}) zwróciło 0 plików")
    if not list(iter_domain_files()):
        problems.append("iter_domain_files() zwróciło 0 plików")
    for name in ("command_handlers", "query_handlers", "repositories", "mappers"):
        if (
            not list(iter_named_dirs("application", name))
            and not list(iter_named_dirs("domain", name))
            and not list(iter_named_dirs("infrastructure", name))
        ):
            problems.append(f"iter_named_dirs(..., {name!r}) zwróciło 0 katalogów")
    return problems


def _iter_bare_layer_references() -> list[str]:
    """Any direct `BASE / "<layer>"` reference in an architecture test that resolves
    to a non-existent top-level directory under BASE."""
    violations: list[str] = []
    pattern = re.compile(r'[(" ]BASE\s*/\s*"(' + "|".join(_LAYER_NAMES) + r')"')
    for txt in _TECHNICAL_MODULES:
        del txt
    for test_file in sorted((BASE / "tests" / "architecture").glob("test_*.py")):
        if test_file.name in _TECHNICAL_MODULES:
            continue
        for line_no, line in enumerate(test_file.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line):
                violations.append(f"{test_file.relative_to(BASE)}:{line_no}: {line.strip()}")
    return violations


def test_architecture_guards_actually_scan_real_code() -> None:
    problems = _assert_iterators_non_empty()
    if not SERVICE_ROOTS:
        problems.append("SERVICE_ROOTS jest puste")
    for service_root in SERVICE_ROOTS:
        if not any(iter_py_files(service_root / layer) for layer in _LAYER_NAMES):
            problems.append(f"{service_root.relative_to(BASE)}: brak plików w warstwach domeny")

    bare = _iter_bare_layer_references()
    problems.extend(bare)
    if problems:
        raise AssertionError(
            architecture_assertion_message(
                "reguła testowana przez test_architecture_guards_actually_scan_real_code",
                "warunek zapisany w asercji musi być spełniony",
                "Architektura/strażniki izolacji muszą skanować realne per-BC ścieżki:\n"
                + "\n".join(problems),
            )
        )
