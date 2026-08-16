"""Koncept: reguła architektoniczna dotycząca naming conventions: test file names are snake case.

Reguła: test sprawdza kontrakt architektoniczny naming conventions: test file names are snake case.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""
from __future__ import annotations

import re

from _arch_helpers import BASE, architecture_assertion_message, iter_py_files

_ALLOWED_CAPS_METHODS = frozenset({'ID', 'DTO', 'VO', 'HTTP', 'JSON', 'YAML', 'XML', 'API', 'URL', 'URI', 'DB', 'SQL', 'ORM', 'CLI', 'GUI', 'UID', 'UUID', 'SHA', 'AES', 'RSA'})
_KNOWN_FILENAME_MISMATCH: frozenset[str] = frozenset({'domain/scheduling/services/dual_layer_dispatcher.py: main class is Inbox (expected inbox.py)', 'domain/scheduling/value_objects/ids.py: main class is SchedulerDefinitionId (expected scheduler_definition_id.py)', 'domain/platform/ports/identity.py: main class is IdGenerator (expected id_generator.py)', 'domain/platform/ports/log.py: main class is Logger (expected logger.py)', 'domain/platform/ports/time.py: main class is Clock (expected clock.py)', 'domain/execution/ports/sub_graph_policy.py: main class is Decision (expected decision.py)', 'domain/execution/ports/sub_graph_security.py: main class is Scope (expected scope.py)', 'domain/execution/services/node_execution_output_interpreter.py: main class is OutputDecision (expected output_decision.py)', 'domain/execution/value_objects/graph_execution_definition.py: main class is NodeExecutionDefinition (expected node_execution_definition.py)'})
_NAMING_CORE_LAYERS = frozenset({'domain/'})
_NAMING_SOFT_AREAS = frozenset({'tests/', '/tests/', '/migrations/versions/', '/config/seed/'})
_KNOWN_ABBREVIATION_VIOLATIONS: frozenset[str] = frozenset({'platform/framework/api/middleware/error_handler.py: function http_exception_handler'})
_ENTITY_SUFFIXES = frozenset({'Entity', 'Event', 'Dto', 'Model', 'Adapter', 'Mapper', 'Service', 'Specification'})

def test_file_names_are_snake_case() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE):
        name = path.stem
        if not re.match('^[a-z0-9_]+$', name):
            violations.append(f'{path.relative_to(BASE)}')
    assert not violations, architecture_assertion_message('reguła testowana przez test_file_names_are_snake_case', 'warunek zapisany w asercji musi być spełniony', 'Python file names must be snake_case:\n' + '\n'.join(violations))
