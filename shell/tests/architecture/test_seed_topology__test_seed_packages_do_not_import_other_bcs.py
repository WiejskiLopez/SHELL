"""Koncept: izolacja seedowania między Bounded Contextami.

Reguła: kod seed subpakietu BC może importować wyłącznie swój własny BC oraz
``shell.platform`` — nigdy innego BC (integracja idzie przez HTTP/event kontrakty).

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from _arch_helpers import BASE, architecture_assertion_message, get_imports, iter_py_files

if TYPE_CHECKING:
    import pathlib

_BCS = frozenset(
    {
        "execution_service",
        "definition_service",
        "session_service",
        "user_service",
        "project_service",
        "scheduling_service",
        "ingestion_service",
    }
)

_BC_DOMAIN_NAME = {
    "user_service": "user",
    "session_service": "session",
    "definition_service": "definition",
    "execution_service": "execution",
    "scheduling_service": "scheduling",
    "project_service": "project",
    "ingestion_service": "ingestion",
}


def _seed_package_path(bc: str) -> pathlib.Path:
    return BASE / bc / "infrastructure" / _BC_DOMAIN_NAME[bc] / "seed"


def _is_cross_bc_import(imp: str, source_bc: str) -> str | None:
    """Return the target BC name when ``imp`` crosses a BC boundary."""
    for bc in _BCS:
        if bc == source_bc:
            continue
        if imp.startswith(f"shell.{bc}."):
            return bc
    return None


def test_seed_packages_do_not_import_other_bcs() -> None:
    violations: list[str] = []
    for source_bc in _BCS:
        seed_path = _seed_package_path(source_bc)
        if not seed_path.exists():
            continue
        for path in iter_py_files(seed_path):
            for imp in get_imports(path):
                target_bc = _is_cross_bc_import(imp, source_bc)
                if target_bc is not None:
                    violations.append(
                        f"{path.relative_to(BASE).as_posix()}: imports {imp!r} (from BC {target_bc})"
                    )
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_seed_packages_do_not_import_other_bcs",
        "seed importuje tylko swój BC oraz shell.platform",
        violations,
    )
