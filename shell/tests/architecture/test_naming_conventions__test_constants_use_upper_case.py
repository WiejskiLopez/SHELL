"""Koncept: reguła architektoniczna dotycząca naming conventions: test constants use upper case.

Reguła: test sprawdza kontrakt architektoniczny naming conventions: test constants use upper case.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""
from __future__ import annotations

import ast

from _arch_helpers import BASE, architecture_assertion_message, iter_py_files, parse_file

_ALLOWED_CAPS_METHODS = frozenset({'ID', 'DTO', 'VO', 'HTTP', 'JSON', 'YAML', 'XML', 'API', 'URL', 'URI', 'DB', 'SQL', 'ORM', 'CLI', 'GUI', 'UID', 'UUID', 'SHA', 'AES', 'RSA'})
_KNOWN_FILENAME_MISMATCH: frozenset[str] = frozenset({'domain/scheduling/services/dual_layer_dispatcher.py: main class is Inbox (expected inbox.py)', 'domain/scheduling/value_objects/ids.py: main class is SchedulerDefinitionId (expected scheduler_definition_id.py)', 'domain/platform/ports/identity.py: main class is IdGenerator (expected id_generator.py)', 'domain/platform/ports/log.py: main class is Logger (expected logger.py)', 'domain/platform/ports/time.py: main class is Clock (expected clock.py)', 'domain/execution/ports/sub_graph_policy.py: main class is Decision (expected decision.py)', 'domain/execution/ports/sub_graph_security.py: main class is Scope (expected scope.py)', 'domain/execution/services/node_execution_output_interpreter.py: main class is OutputDecision (expected output_decision.py)', 'domain/execution/value_objects/graph_execution_definition.py: main class is NodeExecutionDefinition (expected node_execution_definition.py)'})
_NAMING_CORE_LAYERS = frozenset({'domain/'})
_NAMING_SOFT_AREAS = frozenset({'tests/', '/tests/', '/migrations/versions/', '/config/seed/'})
_KNOWN_ABBREVIATION_VIOLATIONS: frozenset[str] = frozenset({'platform/framework/api/middleware/error_handler.py: function http_exception_handler'})
_ENTITY_SUFFIXES = frozenset({'Entity', 'Event', 'Dto', 'Model', 'Adapter', 'Mapper', 'Service', 'Specification'})

def test_constants_use_upper_case() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE):
        rel = path.relative_to(BASE).as_posix()
        if rel.startswith('tests/'):
            continue
        tree = parse_file(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        if name.startswith('_'):
                            name = name.lstrip('_')
                        if name.isupper():
                            continue
                        if name[0].isupper() and (not name.startswith('__')) and isinstance(node.value, (ast.Constant, ast.List, ast.Dict, ast.Set, ast.Tuple)):
                            violations.append(f'{rel}: {target.id}')
    assert not violations, architecture_assertion_message('reguła testowana przez test_constants_use_upper_case', 'warunek zapisany w asercji musi być spełniony', 'Module-level constants must use UPPER_CASE:\n' + '\n'.join(violations))
