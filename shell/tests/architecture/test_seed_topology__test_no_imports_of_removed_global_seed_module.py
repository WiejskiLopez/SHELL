"""Koncept: likwidacja globalnego orchestratora seedów.

Reguła: globalny moduł ``shell.config.seed`` został usunięty na rzecz seedowania
per BC; żaden plik nie może importować zlikwidowanego modułu ani go przywracać.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

from _arch_helpers import BASE, architecture_assertion_message, get_imports, iter_py_files


def test_no_imports_of_removed_global_seed_module() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE):
        for imp in get_imports(path):
            if imp == "shell.config.seed" or imp.startswith("shell.config.seed."):
                violations.append(f"{path.relative_to(BASE).as_posix()}: imports {imp!r}")
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_no_imports_of_removed_global_seed_module",
        "nikt nie importuje zlikwidowanego shell.config.seed",
        violations,
    )
