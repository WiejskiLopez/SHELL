"""Koncept: reguła architektoniczna dotycząca bc container boundaries.

Reguła: test sprawdza kontrakt architektoniczny bc container boundaries.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""
from __future__ import annotations

from _arch_helpers import BASE, architecture_assertion_message, get_imports, iter_py_files

_BC_CONTAINER_ROOTS = {'definition_service': BASE / 'definition_service' / 'bootstrap' / 'definition' / 'container', 'execution_service': BASE / 'execution_service' / 'bootstrap' / 'execution' / 'container', 'project_service': BASE / 'project_service' / 'bootstrap' / 'project' / 'container', 'scheduling_service': BASE / 'scheduling_service' / 'bootstrap' / 'scheduling' / 'container', 'ingestion_service': BASE / 'ingestion_service' / 'bootstrap' / 'ingestion' / 'container', 'session_service': BASE / 'session_service' / 'bootstrap' / 'session' / 'container', 'user_service': BASE / 'user_service' / 'bootstrap' / 'user' / 'container'}
_ALLOWED_CROSS_BC_CONTRACTS = frozenset({'shell.user_service.application.user.user.integration_events', 'shell.user_service.application.user.auth_session.integration_events'})

def _is_allowed_contract(imported: str) -> bool:
    return any(imported == allowed or imported.startswith(allowed + '.') for allowed in _ALLOWED_CROSS_BC_CONTRACTS)

def test_bc_containers_import_only_their_own_bc() -> None:
    violations: list[str] = []
    missing_roots = [name for name, root in _BC_CONTAINER_ROOTS.items() if not root.is_dir()]
    assert not missing_roots, architecture_assertion_message('reguła testowana przez test_bc_containers_import_only_their_own_bc', 'warunek zapisany w asercji musi być spełniony', f'Expected BC container roots are missing: {missing_roots}')
    for bc, container_root in _BC_CONTAINER_ROOTS.items():
        for path in iter_py_files(container_root):
            for imported in get_imports(path):
                for other_bc in _BC_CONTAINER_ROOTS:
                    if other_bc == bc:
                        continue
                    if _is_allowed_contract(imported):
                        continue
                    if imported.startswith((f'shell.{other_bc}.',)):
                        violations.append(f'{path.relative_to(BASE).as_posix()}: imports {imported!r}')
    assert not violations, architecture_assertion_message('reguła testowana przez test_bc_containers_import_only_their_own_bc', 'warunek zapisany w asercji musi być spełniony', 'A BC container may compose only its own BC and platform services:\n' + '\n'.join(violations))
