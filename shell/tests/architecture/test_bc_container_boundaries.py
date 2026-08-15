from __future__ import annotations

from _arch_helpers import BASE, get_imports, iter_py_files

_BC_CONTAINER_ROOTS = {
    "definition": BASE / "definition" / "bootstrap" / "definition" / "container",
    "execution": BASE / "execution" / "bootstrap" / "execution" / "container",
    "project": BASE / "project" / "bootstrap" / "project" / "container",
    "scheduling": BASE / "scheduling" / "bootstrap" / "scheduling" / "container",
    "ingestion": BASE / "ingestion" / "bootstrap" / "ingestion" / "container",
    "session": BASE / "session" / "bootstrap" / "session" / "container",
    "user": BASE / "user" / "bootstrap" / "user" / "container",
}

# Cross-BC integration-event contracts a container may subscribe to (same
# allowlist as test_bc_isolation — public contracts, not implementation code).
_ALLOWED_CROSS_BC_CONTRACTS = frozenset(
    {
        "shell.user_service.application.user.user.integration_events",
        "shell.user_service.application.user.auth_session.integration_events",
    }
)


def _is_allowed_contract(imported: str) -> bool:
    return any(
        imported == allowed or imported.startswith(allowed + ".")
        for allowed in _ALLOWED_CROSS_BC_CONTRACTS
    )


def test_bc_containers_import_only_their_own_bc() -> None:
    violations: list[str] = []

    for bc, container_root in _BC_CONTAINER_ROOTS.items():
        for path in iter_py_files(container_root):
            for imported in get_imports(path):
                for other_bc in _BC_CONTAINER_ROOTS:
                    if other_bc == bc:
                        continue
                    if _is_allowed_contract(imported):
                        continue
                    if imported.startswith(
                        (
                            f"shell.domain.{other_bc}",
                            f"shell.application.{other_bc}",
                            f"shell.infrastructure.{other_bc}",
                            f"shell.{other_bc}.domain.{other_bc}",
                            f"shell.{other_bc}.application.{other_bc}",
                            f"shell.{other_bc}.infrastructure.{other_bc}",
                        )
                    ):
                        violations.append(
                            f"{path.relative_to(BASE).as_posix()}: imports {imported!r}"
                        )

    assert not violations, (
        "A BC container may compose only its own BC and platform services:\n"
        + "\n".join(violations)
    )
