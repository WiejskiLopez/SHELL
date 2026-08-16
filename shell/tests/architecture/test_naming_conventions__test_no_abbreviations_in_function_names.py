"""Koncept: reguła architektoniczna dotycząca naming conventions: test no abbreviations in function names.

Reguła: test sprawdza kontrakt architektoniczny naming conventions: test no abbreviations in function names.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

import ast

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    has_abbreviation,
    is_magic,
    iter_py_files,
    parse_file,
)

_ALLOWED_CAPS_METHODS = frozenset(
    {
        "ID",
        "DTO",
        "VO",
        "HTTP",
        "JSON",
        "YAML",
        "XML",
        "API",
        "URL",
        "URI",
        "DB",
        "SQL",
        "ORM",
        "CLI",
        "GUI",
        "UID",
        "UUID",
        "SHA",
        "AES",
        "RSA",
    }
)
_KNOWN_FILENAME_MISMATCH: frozenset[str] = frozenset(
    {
        "domain/scheduling/services/dual_layer_dispatcher.py: main class is Inbox (expected inbox.py)",
        "domain/scheduling/value_objects/ids.py: main class is SchedulerDefinitionId (expected scheduler_definition_id.py)",
        "domain/platform/ports/identity.py: main class is IdGenerator (expected id_generator.py)",
        "domain/platform/ports/log.py: main class is Logger (expected logger.py)",
        "domain/platform/ports/time.py: main class is Clock (expected clock.py)",
        "domain/execution/ports/sub_graph_policy.py: main class is Decision (expected decision.py)",
        "domain/execution/ports/sub_graph_security.py: main class is Scope (expected scope.py)",
        "domain/execution/services/node_execution_output_interpreter.py: main class is OutputDecision (expected output_decision.py)",
        "domain/execution/value_objects/graph_execution_definition.py: main class is NodeExecutionDefinition (expected node_execution_definition.py)",
    }
)
_NAMING_CORE_LAYERS = frozenset({"domain/"})
_NAMING_SOFT_AREAS = frozenset({"tests/", "/tests/", "/migrations/versions/"})
_KNOWN_ABBREVIATION_VIOLATIONS: frozenset[str] = frozenset(
    {"platform/framework/api/middleware/error_handler.py: function http_exception_handler"}
)
_ENTITY_SUFFIXES = frozenset(
    {"Entity", "Event", "Dto", "Model", "Adapter", "Mapper", "Service", "Specification"}
)


def test_no_abbreviations_in_function_names() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE):
        rel = path.relative_to(BASE).as_posix()
        if rel.startswith("tests/"):
            continue
        tree = parse_file(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if is_magic(node.name):
                    continue
                if node.name.startswith("_"):
                    continue
                if has_abbreviation(node.name):
                    key = f"{rel}: function {node.name}"
                    if key not in _KNOWN_ABBREVIATION_VIOLATIONS:
                        violations.append(key)
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_no_abbreviations_in_function_names",
        "warunek zapisany w asercji musi być spełniony",
        "Function/method names in production code must not use abbreviations:\n"
        + "\n".join(violations),
    )
