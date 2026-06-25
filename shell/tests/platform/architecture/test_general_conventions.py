from __future__ import annotations

import ast
import re

from _arch_helpers import BASE, iter_py_files, parse_file


# ── 1. `from __future__ import annotations` in every file ──────────

_KNOWN_MISSING_FUTURE: frozenset[str] = frozenset({
    "infrastructure/scheduling/persistence/sql/models/base.py",
    "domain/execution/aggregates/task_execution/exceptions/invalid_task_definition_source.py",
    "domain/execution/aggregates/graph_node_execution/exceptions/invalid_node_execution_transition.py",
    "domain/execution/aggregates/graph_node_execution/exceptions/role_not_resolved.py",
    "domain/execution/aggregates/agent_config_execution/exceptions/agent_config_execution_not_found.py",
})


def test_future_annotations_in_every_file() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE):
        rel = path.relative_to(BASE).as_posix()
        if rel in _KNOWN_MISSING_FUTURE:
            continue
        if "tests" in rel or rel.startswith("config/") or rel.startswith("shell.egg-info/"):
            continue
        if "migrations/versions" in rel:
            continue
        tree = parse_file(path)
        if tree is None:
            continue
        has_future = any(
            isinstance(node, ast.ImportFrom)
            and node.module == "__future__"
            and any(alias.name == "annotations" for alias in node.names)
            for node in ast.walk(tree)
        )
        if not has_future:
            violations.append(rel)
    assert not violations, (
        "Production .py files should have `from __future__ import annotations`:\n"
        + "\n".join(violations)
    )


# ── 2. Function/parameters have type hints ────────────────────────

_PATHS_WITHOUT_TYPE_HINTS: frozenset[str] = frozenset({
    "infrastructure/scheduling/services/scheduler_service.py",
    "infrastructure/platform/persistence/sql_alchemy_uow.py",
    "infrastructure/platform/persistence/sql/rag_search/rag_search_strategy.py",
    "infrastructure/execution/persistence/sql/repositories/sql_graph_execution_repository.py",
    "infrastructure/execution/persistence/sql/repositories/sql_graph_node_execution_repository.py",
    "infrastructure/definition/persistence/sql/repositories/sql_graph_definition_repository.py",
    "config/seed/dev_data.py",
})


def test_functions_have_type_hints() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE):
        rel = path.relative_to(BASE).as_posix()
        if rel in _PATHS_WITHOUT_TYPE_HINTS:
            continue
        if "tests" in rel.split("/") or "migrations/versions" in rel:
            continue
        if rel.startswith("shell.egg-info/"):
            continue
        tree = parse_file(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == "__init__":
                    continue
                has_return_hint = node.returns is not None
                has_param_hints = all(
                    arg.annotation is not None
                    for arg in node.args.args
                    if arg.arg != "self" and arg.arg != "cls"
                )
                if not has_return_hint or not has_param_hints:
                    violations.append(
                        f"{rel}: {node.name} (return_hint={has_return_hint}, param_hints={has_param_hints})"
                    )
    assert not violations, (
        "All functions must have type hints:\n"
        + "\n".join(violations)
    )


# ── 3. __init__.py only re-exports ────────────────────────────────


_KNOWN_INIT_DEFINITIONS: frozenset[str] = frozenset({
})


def test_init_files_only_re_export() -> None:
    violations: list[str] = []
    _INIT_KNOW_DEFINE = frozenset({
        "domain/platform/base/__init__.py",
        "domain/platform/events/__init__.py",
        "domain/platform/ports/__init__.py",
        "infrastructure/platform/persistence/sql/models/base.py",
        "infrastructure/platform/logging/__init__.py",
        "infrastructure/platform/time/__init__.py",
        "infrastructure/platform/persistence/sql/__init__.py",
        "infrastructure/platform/persistence/sql/mappers/__init__.py",
        "infrastructure/platform/persistence/migrations/sql/__init__.py",
        "infrastructure/platform/logging/stdlib_logger/__init__.py",
        "framework/execution/api/routers/task_executions/__init__.py",
        "framework/execution/api/routers/workflows/__init__.py",
    })
    for init_file in BASE.rglob("__init__.py"):
        rel = init_file.relative_to(BASE).as_posix()
        if rel in _INIT_KNOW_DEFINE:
            continue
        tree = parse_file(init_file)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name == "Base" and "sql" in str(init_file):
                    continue
                key = f"{rel}: defines {node.name}"
                if key not in _KNOWN_INIT_DEFINITIONS:
                    violations.append(key)
    assert not violations, (
        "__init__.py should only re-export, not define classes/functions:\n"
        + "\n".join(violations)
    )


# ── 4. # noqa has rule code + reason ──────────────────────────────

_NOQA_KNOWN_INVALID: frozenset[str] = frozenset({
    "tests/platform/architecture/conftest.py",
})


_NOQA_KNOWN_WITHOUT_REASON: frozenset[str] = frozenset({
    "tests/platform/architecture/test_general_conventions.py:136",
    "tests/platform/architecture/test_general_conventions.py:167",
    "tests/platform/architecture/test_general_conventions.py:168",
    "tests/platform/architecture/test_general_conventions.py:174",
    "tests/platform/architecture/test_general_conventions.py:175",
    "tests/platform/architecture/test_general_conventions.py:227",
    "tests/platform/architecture/test_general_conventions.py:232",
    "infrastructure/execution/persistence/memory/in_memory_agent_config_execution_repository.py:10",
    "infrastructure/execution/persistence/memory/in_memory_agent_config_execution_repository.py:13",
    "infrastructure/execution/persistence/memory/in_memory_graph_node_transition_execution_repository.py:7",
    "infrastructure/execution/persistence/memory/in_memory_graph_node_transition_execution_repository.py:10",
    "infrastructure/execution/persistence/memory/in_memory_graph_node_transition_execution_repository.py:16",
    "infrastructure/execution/persistence/sql/services/node_result_query_service.py:26",
})


def test_noqa_has_justification() -> None:
    violations: list[str] = []
    _TEST_FILES = frozenset({"test_general_conventions.py", "test_enterprise_patterns.py", "test_domain_structure.py"})
    for path in iter_py_files(BASE):
        rel = path.relative_to(BASE).as_posix()
        if rel in _NOQA_KNOWN_INVALID:
            continue
        if path.name in _TEST_FILES:
            continue
        content = path.read_text(encoding="utf-8")
        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            if "# noqa" in stripped:
                has_code = bool(re.search(r"# noqa:\s*\w+", stripped))
                has_reason = bool(re.search(r"(--|—|–|-)", stripped))
                if not has_code or not has_reason:
                    key = f"{rel}:{i}"
                    if key not in _NOQA_KNOWN_WITHOUT_REASON:
                        violations.append(f"{rel}:{i}: {stripped}")
    assert not violations, (
        "Each # noqa must include rule code and justification (-- reason):\n"
        + "\n".join(violations)
    )


# ── 5. No comments in production code ─────────────────────────────

_COMMENT_KNOWN_EXCEPTIONS: frozenset[str] = frozenset({
    "infrastructure/platform/configuration/shell_config.py",
    "infrastructure/platform/default_implementations/sub_graph_defaults.py",
    "infrastructure/platform/persistence/migrations/sql/env.py",
    "infrastructure/platform/persistence/migrations/sql/versions/001_initial.py",
    "infrastructure/platform/messaging/processor/inbox_processor.py",
    "infrastructure/execution/filesystem/envelope_archive_fs.py",
    "infrastructure/execution/filesystem/workspace.py",
    "infrastructure/execution/process/command_builder.py",
    "infrastructure/execution/process/subprocess_runner.py",
    "framework/platform/api/app.py",
    "framework/platform/cli/main.py",
    "framework/execution/api/routers/envelopes.py",
    "framework/execution/api/routers/graph_node_execution.py",
    "domain/platform/value_objects/status.py",
    "domain/execution/aggregates/graph_execution/graph_execution.py",
    "domain/execution/aggregates/graph_node_execution/graph_node_execution.py",
    "domain/execution/aggregates/task_execution/task_execution.py",
    "domain/definition/repositories/rag_repository.py",
    "domain/definition/repositories/runner_config_repository.py",
    "config/seed/dev_data.py",
    "bootstrap/platform/container/events_container.py",
    "bootstrap/platform/container/infrastructure_container.py",
    "bootstrap/platform/factory/command_factory.py",
    "bootstrap/platform/factory/event_factory.py",
    "bootstrap/platform/factory/query_factory.py",
    "bootstrap/execution/factory/application_factory.py",
    "bootstrap/execution/cli/command/smoke_command.py",
    "application/execution/command_handlers/run_graph_node_execution_handler.py",
    "application/execution/event_handlers/graph_node_execution_worker.py",
    "application/definition/command_handlers/index_document_handler.py",
})


def test_no_comments_in_production_code() -> None:
    violations: list[str] = []
    _CHECK_LAYERS = frozenset({"domain", "application"})
    for layer in _CHECK_LAYERS:
        for path in iter_py_files(BASE / layer):
            rel = path.relative_to(BASE).as_posix()
            if rel in _COMMENT_KNOWN_EXCEPTIONS:
                continue
            content = path.read_text(encoding="utf-8")
            for i, line in enumerate(content.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#") and "# noqa" not in stripped:
                    if not stripped.startswith("#!") and not stripped.startswith("# -*-"):
                        if re.match(r"# \w", stripped):
                            violations.append(f"{rel}:{i}: {stripped[:80]}")
    assert not violations, (
        "Domain/application code should avoid comments (except # noqa):\n"
        + "\n".join(violations)
    )
