from __future__ import annotations

import ast
import re

from _arch_helpers import (
    BASE,
    find_classes,
    has_abbreviation,
    is_magic,
    iter_py_files,
    parse_file,
    to_snake_case,
)

# ── 1. Classes use PascalCase ─────────────────────────────────────


def test_classes_use_pascal_case() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if node.name[0].islower():
                violations.append(f"{path.relative_to(BASE)}: class {node.name}")
    assert not violations, "All classes must use PascalCase:\n" + "\n".join(violations)


# ── 2. Functions/methods use snake_case ──────────────────────────

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


def test_methods_use_snake_case() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = node.name
                if is_magic(name):
                    continue
                if name.startswith("_") and not name.startswith("__"):
                    name = name[1:]
                if name.startswith("__"):
                    continue
                if name in _ALLOWED_CAPS_METHODS:
                    continue
                if name[0].isupper():
                    violations.append(f"{path.relative_to(BASE)}: function {name}")
    assert not violations, "Functions/methods must use snake_case:\n" + "\n".join(violations)


# ── 3. File names are snake_case ──────────────────────────────────


def test_file_names_are_snake_case() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE):
        name = path.stem
        if not re.match(r"^[a-z0-9_]+$", name):
            violations.append(f"{path.relative_to(BASE)}")
    assert not violations, "Python file names must be snake_case:\n" + "\n".join(violations)


# ── 4. File name matches the main class in the file ───────────────


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
_NAMING_SOFT_AREAS = frozenset({"tests/", "/tests/", "/migrations/versions/", "/config/seed/"})


def test_filename_matches_class_name() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE):
        rel = path.relative_to(BASE).as_posix()
        if path.stem == "__init__":
            continue
        if not any(rel.startswith(layer) for layer in _NAMING_CORE_LAYERS):
            continue
        if any(a in rel for a in _NAMING_SOFT_AREAS):
            continue
        tree = parse_file(path)
        if tree is None:
            continue
        classes = list(find_classes(tree))
        if not classes:
            continue
        main_class = max(classes, key=lambda c: len(c.body))
        if main_class.name.startswith("_"):
            continue
        expected_stem = to_snake_case(main_class.name)
        if path.stem != expected_stem and path.stem != expected_stem.rstrip("_"):
            any_match = any(to_snake_case(c.name) == path.stem for c in classes)
            if any_match:
                continue
            key = f"{rel}: main class is {main_class.name} (expected {expected_stem}.py)"
            if key not in _KNOWN_FILENAME_MISMATCH:
                violations.append(key)
    assert not violations, (
        "File name should match the main class (PascalCase -> snake_case):\n"
        + "\n".join(violations)
    )


# ── 5. Constants use UPPER_CASE ────────────────────────────────────


def test_constants_use_upper_case() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE):
        rel = path.relative_to(BASE).as_posix()
        if rel.startswith("tests/"):
            continue
        tree = parse_file(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        if name.startswith("_"):
                            name = name.lstrip("_")
                        if name.isupper():
                            continue
                        if (
                            name[0].isupper()
                            and not name.startswith("__")
                            and isinstance(
                                node.value, (ast.Constant, ast.List, ast.Dict, ast.Set, ast.Tuple)
                            )
                        ):
                            violations.append(f"{rel}: {target.id}")
    assert not violations, "Module-level constants must use UPPER_CASE:\n" + "\n".join(violations)


# ── 6. No abbreviations in names ──────────────────────────────────

_KNOWN_ABBREVIATION_VIOLATIONS: frozenset[str] = frozenset(
    {
        "platform/framework/api/middleware/error_handler.py: function http_exception_handler",
    }
)


def test_no_abbreviations_in_class_names() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if has_abbreviation(node.name):
                key = f"{path.relative_to(BASE)}: class {node.name}"
                if key not in _KNOWN_ABBREVIATION_VIOLATIONS:
                    violations.append(key)
    assert not violations, "Class names must not use abbreviations:\n" + "\n".join(violations)


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
    assert not violations, (
        "Function/method names in production code must not use abbreviations:\n"
        + "\n".join(violations)
    )


# ── 7. Handler classes end with 'Handler' ─────────────────────────


def test_handler_classes_end_with_handler() -> None:
    violations: list[str] = []
    for handler_dir in [
        BASE / "application" / "command_handlers",
        BASE / "application" / "query_handlers",
        BASE / "application" / "event_handlers",
    ]:
        if not handler_dir.exists():
            continue
        for path in iter_py_files(handler_dir):
            tree = parse_file(path)
            if tree is None:
                continue
            for node in find_classes(tree):
                if not node.name.endswith("Handler"):
                    violations.append(f"{path.relative_to(BASE)}: class {node.name}")
    assert not violations, "Handler classes must end with 'Handler':\n" + "\n".join(violations)


# ── 8. Repository port classes end with 'Repository' ──────────────


def test_repository_ports_end_with_repository() -> None:
    violations: list[str] = []
    for repos_dir in (BASE / "domain").rglob("repositories"):
        if not repos_dir.is_dir():
            continue
        for path in iter_py_files(repos_dir):
            tree = parse_file(path)
            if tree is None:
                continue
            for node in find_classes(tree):
                if not node.name.endswith("Repository"):
                    violations.append(f"{path.relative_to(BASE)}: class {node.name}")
    assert not violations, "Repository port classes must end with 'Repository':\n" + "\n".join(
        violations
    )


# ── 9. Entity classes use suffix naming where applicable ──────────

_ENTITY_SUFFIXES = frozenset(
    {"Entity", "Event", "Dto", "Model", "Adapter", "Mapper", "Service", "Specification"}
)


def test_domain_entity_no_suffix_overload() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE / "domain"):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            # Aggregate root entities should not have "Entity" suffix
            if node.name.endswith("Entity"):
                for base_node in node.bases:
                    if isinstance(base_node, ast.Name) and base_node.id in {
                        "AggregateRoot",
                        "Entity",
                    }:
                        violations.append(f"{path.relative_to(BASE)}: class {node.name}")
    assert not violations, (
        "Direct entity/aggregate classes should not have 'Entity' suffix in their name:\n"
        + "\n".join(violations)
    )
