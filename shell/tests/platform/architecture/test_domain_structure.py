from __future__ import annotations

import ast

from _arch_helpers import (
    BASE,
    extends_any_base,
    find_classes,
    has_public_setter,
    has_slots,
    is_frozen_dataclass,
    iter_py_files,
    parse_file,
)

_VO_BASES = {"ValueObject"}
_ENTITY_BASES = {"Entity"}
_AGGREGATE_BASES = {"AggregateRoot"}
_EVENT_BASES = {"DomainEvent"}
_DOMAIN_BASES = _VO_BASES | _ENTITY_BASES | _AGGREGATE_BASES | _EVENT_BASES
_SPEC_BASES = {"Specification"}


def _inherits_any(node: ast.ClassDef, bases: set[str]) -> bool:
    return extends_any_base(node, bases)


# ── 1. VO: @dataclass(frozen=True, slots=True) ────────────────────

_KNOWN_VO_NO_SLOTS: frozenset[str] = frozenset({})


def _is_strenum(node: ast.ClassDef) -> bool:
    """Check if a class extends StrEnum (which can't have slots=True)."""
    return any(isinstance(base, ast.Name) and base.id == "StrEnum" for base in node.bases)


def test_value_objects_are_frozen_dataclass_with_slots() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE / "domain"):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not _inherits_any(node, _VO_BASES):
                continue
            if _is_strenum(node):
                continue
            if not is_frozen_dataclass(node, require_slots=True):
                key = f"{path.relative_to(BASE)}: class {node.name}"
                if key not in _KNOWN_VO_NO_SLOTS:
                    violations.append(key)
    assert not violations, (
        "ValueObjects must be @dataclass(frozen=True, slots=True):\n" + "\n".join(violations)
    )


# ── 2. Entity/AggregateRoot are NOT @dataclass ────────────────────


def test_entities_are_not_dataclass() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE / "domain"):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not _inherits_any(node, _ENTITY_BASES | _AGGREGATE_BASES):
                continue
            if is_frozen_dataclass(node) or _has_dataclass_decorator(node):
                violations.append(f"{path.relative_to(BASE)}: class {node.name}")
    assert not violations, (
        "Entities/AggregateRoots must NOT be @dataclass (identity-based equality):\n"
        + "\n".join(violations)
    )


def _has_dataclass_decorator(node: ast.ClassDef) -> bool:
    for dec in node.decorator_list:
        if isinstance(dec, ast.Name) and dec.id == "dataclass":
            return True
        if (
            isinstance(dec, ast.Call)
            and isinstance(dec.func, ast.Name)
            and dec.func.id == "dataclass"
        ):
            return True
    return False


# ── 3. Entity/Aggregate has __slots__ ─────────────────────────────


def test_entities_have_slots() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE / "domain"):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not _inherits_any(node, _ENTITY_BASES | _AGGREGATE_BASES):
                continue
            if not has_slots(node):
                violations.append(f"{path.relative_to(BASE)}: class {node.name}")
    assert not violations, "Entities/AggregateRoots must define __slots__:\n" + "\n".join(
        violations
    )


# ── 4. No public setters in entities/aggregates ───────────────────


def test_no_public_setters() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE / "domain"):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not _inherits_any(node, _ENTITY_BASES | _AGGREGATE_BASES):
                continue
            if has_public_setter(node):
                violations.append(f"{path.relative_to(BASE)}: class {node.name}")
    assert not violations, "Entities/AggregateRoots must not have public setters:\n" + "\n".join(
        violations
    )


# ── 5. Init params assigned to private attrs with _ prefix ────────


_KNOWN_PUBLIC_INIT_ATTRS: frozenset[str] = frozenset({})


def test_entity_init_uses_private_attrs() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE / "domain"):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not _inherits_any(node, _AGGREGATE_BASES):
                continue
            for stmt in node.body:
                if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
                    for line in ast.walk(stmt):
                        if (
                            isinstance(line, ast.Attribute)
                            and isinstance(line.value, ast.Name)
                            and line.value.id == "self"
                            and not line.attr.startswith("_")
                        ):
                            key = f"{path.relative_to(BASE)}: {node.name}.__init__ assigns to public {line.attr!r}"
                            if key not in _KNOWN_PUBLIC_INIT_ATTRS:
                                violations.append(key)
    assert not violations, (
        "Entity/AggregateRoot __init__ must assign to private attributes with _ prefix:\n"
        + "\n".join(violations)
    )


# ── 6. Domain Event: @dataclass(frozen=True), extends DomainEvent ──

_KNOWN_NON_EVENT_DOMAIN_CLASSES: frozenset[str] = frozenset({})


def test_domain_events_are_frozen_dataclass() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE / "domain"):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not _inherits_any(node, _EVENT_BASES):
                continue
            if not is_frozen_dataclass(node):
                key = f"{path.relative_to(BASE)}: class {node.name}"
                if key not in _KNOWN_NON_EVENT_DOMAIN_CLASSES:
                    violations.append(key)
    assert not violations, "DomainEvents must be @dataclass(frozen=True):\n" + "\n".join(violations)


# ── 7. Mutating methods in aggregates append_event() ──────────────

_KNOWN_NO_EVENT_EMIT: frozenset[str] = frozenset(
    {
        "domain/execution/aggregates/agent_config_execution/agent_config_execution.py: AgentConfigExecution.update_config",
        "domain/execution/aggregates/envelope/envelope.py: Envelope.archive",
        "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.mark_verifying",
        "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.hold_initialization",
        "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.fail_initialization",
        "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.suspend",
        "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.resume",
        "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.create_main_round",
        "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.create_sub_graph",
        "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.prepare_node_definitions",
        "domain/execution/aggregates/graph_execution_state/graph_execution_state.py: GraphExecutionState.get",
        "domain/execution/aggregates/graph_execution_state/graph_execution_state.py: GraphExecutionState.patch",
        "domain/execution/aggregates/graph_execution_state/graph_execution_state.py: GraphExecutionState.clear",
        "domain/execution/aggregates/graph_execution_state/graph_execution_state.py: GraphExecutionState.merge",
        "domain/execution/aggregates/graph_execution_state/graph_execution_state.py: GraphExecutionState.snapshot",
        "domain/execution/aggregates/graph_execution_state/graph_execution_state.py: GraphExecutionState.supersede",
        "domain/execution/aggregates/graph_node_execution_state/graph_node_execution_state.py: GraphNodeExecutionState.get",
        "domain/execution/aggregates/graph_node_execution_state/graph_node_execution_state.py: GraphNodeExecutionState.patch",
        "domain/execution/aggregates/graph_node_execution_state/graph_node_execution_state.py: GraphNodeExecutionState.clear",
        "domain/execution/aggregates/graph_node_execution_state/graph_node_execution_state.py: GraphNodeExecutionState.snapshot",
        "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.create_sequence",
        "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.create_conditional",
        "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.create_loop",
        "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.create_spawn_subgraph",
        "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.create_error_handler",
        "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.create_timeout",
        "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.create_default",
        "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.skip",
        "domain/execution/aggregates/task_execution/task_execution.py: TaskExecution.increment_cycle",
        "domain/execution/aggregates/task_execution/task_execution.py: TaskExecution.rename",
        "domain/execution/aggregates/task_execution/task_execution.py: TaskExecution.execute_in_workflow",
        "domain/execution/aggregates/task_execution/task_execution.py: TaskExecution.prepare_workspace",
        "domain/execution/aggregates/session_execution_state/session_execution_state.py: SessionExecutionState.supersede",
        "domain/execution/aggregates/task_execution_state/task_execution_state.py: TaskExecutionState.supersede",
        "domain/execution/aggregates/user_execution_state/user_execution_state.py: UserExecutionState.supersede",
        "domain/session/aggregates/session_state/session_state.py: SessionState.get",
        "domain/session/aggregates/session_state/session_state.py: SessionState.patch",
        "domain/session/aggregates/session_state/session_state.py: SessionState.clear",
        "domain/session/aggregates/session_state/session_state.py: SessionState.snapshot",
        "domain/execution/aggregates/workflow_state/workflow_state.py: WorkflowState.get",
        "domain/execution/aggregates/workflow_state/workflow_state.py: WorkflowState.patch",
        "domain/execution/aggregates/workflow_state/workflow_state.py: WorkflowState.clear",
        "domain/execution/aggregates/workflow_state/workflow_state.py: WorkflowState.snapshot",
    }
)


def _is_property(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for dec in node.decorator_list:
        if isinstance(dec, ast.Attribute) and dec.attr == "getter":
            return True
        if isinstance(dec, ast.Name) and dec.id == "property":
            return True
    return False


def test_mutating_methods_emit_events() -> None:
    violations: list[str] = []
    _NON_MUTATING = frozenset(
        {
            "__init__",
            "restore",
            "pull_events",
            "to_dict",
            "new",
            "create",
            "generate",
            "matches_trigger",
        }
    )
    for path in iter_py_files(BASE / "domain"):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not _inherits_any(node, _AGGREGATE_BASES):
                continue
            for stmt in node.body:
                if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if stmt.name in _NON_MUTATING:
                    continue
                if stmt.name.startswith("_"):
                    continue
                if _is_property(stmt):
                    continue
                source = ast.unparse(stmt)
                if "append_event(" not in source:
                    key = f"{path.relative_to(BASE).as_posix()}: {node.name}.{stmt.name}"
                    if key not in _KNOWN_NO_EVENT_EMIT:
                        violations.append(f"{key} does not call append_event()")
    assert not violations, (
        "Public mutating methods in aggregates must call append_event():\n" + "\n".join(violations)
    )


# ── 9. Guard clauses at the start of mutating methods ──────────────

_KNOWN_NO_GUARD: frozenset[str] = frozenset(
    {
        "domain/scheduling/aggregates/scheduler_definition/scheduler_definition.py: SchedulerDefinition.matches_trigger",
        "domain/scheduling/aggregates/scheduler_execution/scheduler_execution.py: SchedulerExecution.start",
        "domain/scheduling/aggregates/scheduler_execution/scheduler_execution.py: SchedulerExecution.complete",
        "domain/scheduling/aggregates/scheduler_execution/scheduler_execution.py: SchedulerExecution.fail",
        "domain/scheduling/aggregates/scheduler_execution/scheduler_execution.py: SchedulerExecution.skip",
        "domain/execution/aggregates/agent_config_execution/agent_config_execution.py: AgentConfigExecution.update_config",
        "domain/execution/aggregates/envelope/envelope.py: Envelope.transition_stage",
        "domain/execution/aggregates/envelope/envelope.py: Envelope.deliver_to",
        "domain/execution/aggregates/envelope/envelope.py: Envelope.archive",
        "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.initialize",
        "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.create_main_round",
        "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.prepare_node_definitions",
        "domain/execution/aggregates/graph_execution_state/graph_execution_state.py: GraphExecutionState.update",
        "domain/execution/aggregates/graph_execution_state/graph_execution_state.py: GraphExecutionState.get",
        "domain/execution/aggregates/graph_execution_state/graph_execution_state.py: GraphExecutionState.delete",
        "domain/execution/aggregates/graph_execution_state/graph_execution_state.py: GraphExecutionState.patch",
        "domain/execution/aggregates/graph_execution_state/graph_execution_state.py: GraphExecutionState.clear",
        "domain/execution/aggregates/graph_execution_state/graph_execution_state.py: GraphExecutionState.merge",
        "domain/execution/aggregates/graph_execution_state/graph_execution_state.py: GraphExecutionState.snapshot",
        "domain/execution/aggregates/graph_execution_state/graph_execution_state.py: GraphExecutionState.supersede",
        "domain/execution/aggregates/graph_node_execution_state/graph_node_execution_state.py: GraphNodeExecutionState.update",
        "domain/execution/aggregates/graph_node_execution_state/graph_node_execution_state.py: GraphNodeExecutionState.get",
        "domain/execution/aggregates/graph_node_execution_state/graph_node_execution_state.py: GraphNodeExecutionState.delete",
        "domain/execution/aggregates/graph_node_execution_state/graph_node_execution_state.py: GraphNodeExecutionState.patch",
        "domain/execution/aggregates/graph_node_execution_state/graph_node_execution_state.py: GraphNodeExecutionState.clear",
        "domain/execution/aggregates/graph_node_execution_state/graph_node_execution_state.py: GraphNodeExecutionState.snapshot",
        "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.create_sequence",
        "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.create_conditional",
        "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.create_loop",
        "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.create_spawn_subgraph",
        "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.create_error_handler",
        "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.create_timeout",
        "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.create_default",
        "domain/execution/aggregates/task_execution/task_execution.py: TaskExecution.increment_cycle",
        "domain/execution/aggregates/task_execution/task_execution.py: TaskExecution.rename",
        "domain/execution/aggregates/task_execution/task_execution.py: TaskExecution.execute_in_workflow",
        "domain/execution/aggregates/task_execution/task_execution.py: TaskExecution.prepare_workspace",
        "domain/execution/aggregates/session_execution_state/session_execution_state.py: SessionExecutionState.supersede",
        "domain/execution/aggregates/task_execution_state/task_execution_state.py: TaskExecutionState.supersede",
        "domain/execution/aggregates/user_execution_state/user_execution_state.py: UserExecutionState.supersede",
        "domain/session/aggregates/session/session.py: Session.open",
        "domain/session/aggregates/session_state/session_state.py: SessionState.update",
        "domain/session/aggregates/session_state/session_state.py: SessionState.get",
        "domain/session/aggregates/session_state/session_state.py: SessionState.delete",
        "domain/session/aggregates/session_state/session_state.py: SessionState.patch",
        "domain/session/aggregates/session_state/session_state.py: SessionState.clear",
        "domain/session/aggregates/session_state/session_state.py: SessionState.snapshot",
        "domain/execution/aggregates/workflow_state/workflow_state.py: WorkflowState.update",
        "domain/execution/aggregates/workflow_state/workflow_state.py: WorkflowState.get",
        "domain/execution/aggregates/workflow_state/workflow_state.py: WorkflowState.delete",
        "domain/execution/aggregates/workflow_state/workflow_state.py: WorkflowState.patch",
        "domain/execution/aggregates/workflow_state/workflow_state.py: WorkflowState.clear",
        "domain/execution/aggregates/workflow_state/workflow_state.py: WorkflowState.snapshot",
    }
)


def test_mutating_methods_have_guard() -> None:
    violations: list[str] = []
    _NON_MUTATING = frozenset(
        {
            "__init__",
            "restore",
            "pull_events",
            "to_dict",
            "new",
            "create",
            "generate",
            "of",
            "matches_trigger",
        }
    )
    for path in iter_py_files(BASE / "domain"):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not _inherits_any(node, _AGGREGATE_BASES):
                continue
            for stmt in node.body:
                if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if stmt.name in _NON_MUTATING:
                    continue
                if stmt.name.startswith("_"):
                    continue
                if _is_property(stmt):
                    continue
                body = stmt.body
                has_guard = False
                for line in body:
                    if isinstance(line, ast.If) and _is_raise_body(line):
                        has_guard = True
                        break
                if not has_guard:
                    key = f"{path.relative_to(BASE).as_posix()}: {node.name}.{stmt.name}"
                    if key not in _KNOWN_NO_GUARD:
                        violations.append(key)
    assert not violations, (
        "Mutating methods in entities/aggregates should start with a guard clause (if ... raise):\n"
        + "\n".join(violations)
    )


def _is_raise_body(node: ast.If) -> bool:
    def _has_raise(stmts: list[ast.stmt]) -> bool:
        return any(isinstance(s, ast.Raise) for s in stmts)

    return _has_raise(node.body) or _has_raise(node.orelse)


# ── 10. Domain events use past-tense naming ────────────────────────

_KNOWN_PAST_EVENTS: frozenset[str] = frozenset(
    {
        "domain/execution/aggregates/graph_execution/events/graph_execution_ready_event.py: class GraphExecutionReadyEvent",
    }
)


def test_domain_event_past_tense_naming() -> None:
    import re

    violations: list[str] = []
    pattern = re.compile(
        r".*(ed|ted|led|ned|ged|ked|zed|hed|ped|bed|ved|wed|ched|gged|pped|tted|lled|rred|nned|mmed)$",
        re.IGNORECASE,
    )
    for path in iter_py_files(BASE / "domain"):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not _inherits_any(node, _EVENT_BASES):
                continue
            key = f"{path.relative_to(BASE).as_posix()}: class {node.name}"
            if key in _KNOWN_PAST_EVENTS:
                continue
            if not node.name.endswith("Event"):
                continue
            event_name = node.name[:-5]
            if not pattern.match(event_name):
                violations.append(f"{path.relative_to(BASE)}: class {node.name}")
    assert not violations, (
        "Domain events should use past-tense naming (e.g. WorkflowStartedEvent):\n"
        + "\n".join(violations)
    )


# ── 11. Specification extends Specification[T] ─────────────────────


def test_specifications_extend_specification() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE / "domain"):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not node.name.endswith("Specification"):
                continue
            if not _inherits_any(node, _SPEC_BASES):
                violations.append(f"{path.relative_to(BASE)}: class {node.name}")
    assert not violations, "Specifications must extend Specification[T]:\n" + "\n".join(violations)


# ── 12. Collections returned as copies ─────────────────────────────

_KNOWN_COLLECTION_RETURN_ISSUES: frozenset[str] = frozenset({})


def test_collections_returned_as_copies() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE / "domain"):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not _inherits_any(node, _ENTITY_BASES | _AGGREGATE_BASES):
                continue
            for stmt in node.body:
                if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if stmt.name.startswith("_"):
                    continue
                for line in ast.walk(stmt):
                    if isinstance(line, ast.Return) and line.value:
                        ret_src = ast.unparse(line.value)
                        if _is_collection_type(line.value) and not _is_copy_pattern(line.value):
                            key = f"{path.relative_to(BASE)}: {node.name}.{stmt.name} returns {ret_src}"
                            if key not in _KNOWN_COLLECTION_RETURN_ISSUES:
                                violations.append(key)
    assert not violations, (
        "Properties returning collections should return copies (use .copy(), list(...), tuple(...), [:]):\n"
        + "\n".join(violations)
    )


def _is_collection_type(node: ast.AST) -> bool:
    src = ast.unparse(node)
    return bool(
        src.startswith("self._")
        and any(keyword in src for keyword in ["list", "dict", "set", "tuple", "collections"])
    )


def _is_copy_pattern(node: ast.AST) -> bool:
    src = ast.unparse(node)
    return ".copy()" in src or "list(" in src or "tuple(" in src or "[:]" in src


# ── 13. Domain Service is stateless ────────────────────────────────


_KNOWN_SVC_STATEFUL: frozenset[str] = frozenset(
    {
        "domain/execution/services/sub_graph_execution_service.py: class SubGraphExecutionService has state: ['_clock', '_definition_provider', '_governance', '_id_generator', '_logger', '_observer', '_security', '_unit_of_work', '_versioning']",
    }
)


def test_domain_services_are_stateless() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE / "domain"):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not node.name.endswith("Service"):
                continue
            if _inherits_any(node, _DOMAIN_BASES):
                continue
            state_attrs = set()
            for stmt in node.body:
                if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
                    for line in ast.walk(stmt):
                        if (
                            isinstance(line, ast.Attribute)
                            and isinstance(line.value, ast.Name)
                            and line.value.id == "self"
                        ):
                            state_attrs.add(line.attr)
            non_dep_attrs = [a for a in state_attrs if not a.endswith("_")]
            non_dep_names = sorted(non_dep_attrs)
            if non_dep_names:
                key = f"{path.relative_to(BASE).as_posix()}: class {node.name} has state: {non_dep_names}"
                if key not in _KNOWN_SVC_STATEFUL:
                    violations.append(key)
    assert not violations, (
        "Domain services must be stateless (no state beyond injected dependencies):\n"
        + "\n".join(violations)
    )


# ── 14. Aggregate references other aggregates by ID only ───────────


_KNOWN_ID_ONLY_VIOLATIONS: frozenset[str] = frozenset({})


def _extract_type_names(annotation: ast.AST) -> list[str]:
    """Extract simple type names from an annotation AST."""
    if isinstance(annotation, ast.Name):
        return [annotation.id]
    if isinstance(annotation, ast.Subscript):
        names = []
        if isinstance(annotation.value, ast.Name):
            names.append(annotation.value.id)
        if isinstance(annotation.slice, ast.Tuple):
            for elt in annotation.slice.elts:
                names.extend(_extract_type_names(elt))
        else:
            names.extend(_extract_type_names(annotation.slice))
        return names
    if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
        return _extract_type_names(annotation.left) + _extract_type_names(annotation.right)
    if isinstance(annotation, ast.Attribute):
        return [annotation.attr]
    return []


def test_aggregate_references_by_id_only() -> None:
    violations: list[str] = []
    _AGGREGATE_CLASS_NAMES = frozenset(
        {"Workflow", "TaskExecution", "GraphExecution", "GraphNodeExecution", "WorkflowState"}
    )
    _KNOWN_INTERNAL_ENTITY_PREFIXES: set[str] = set()
    for path in iter_py_files(BASE / "domain"):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not _inherits_any(node, _AGGREGATE_BASES):
                continue
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and stmt.annotation:
                    ann_src = ast.unparse(stmt.annotation)
                    if ann_src.endswith("Id"):
                        continue
                    type_names = _extract_type_names(stmt.annotation)
                    pure_agg_names = [
                        t
                        for t in type_names
                        if t in _AGGREGATE_CLASS_NAMES
                        and not any(
                            t.startswith(prefix) for prefix in _KNOWN_INTERNAL_ENTITY_PREFIXES
                        )
                    ]
                    if pure_agg_names:
                        key = f"{path.relative_to(BASE).as_posix()}: {node.name}.{ast.unparse(stmt.target)}: {ann_src}"
                        if key not in _KNOWN_ID_ONLY_VIOLATIONS:
                            violations.append(key)
    assert not violations, (
        "Aggregates should reference other aggregates by ID only (not by object reference):\n"
        + "\n".join(violations)
    )


# ── 15. No primitive types in Entity/Aggregate instance fields ─────

_PRIMITIVE_TYPES: frozenset[str] = frozenset(
    {
        "str",
        "int",
        "bool",
        "float",
        "bytes",
        "Any",
        "datetime",
        "Decimal",
        "Path",
        "date",
        "time",
        "timedelta",
        "UUID",
    }
)
_COLLECTION_TYPES: frozenset[str] = frozenset({"dict", "list", "set", "tuple", "frozenset"})


_KNOWN_DOMAIN_BASE_TYPES: frozenset[str] = frozenset(
    {
        "ValueObject",
        "Entity",
        "AggregateRoot",
        "DomainEvent",
        "Protocol",
        "ABC",
        "Self",
        "type",
    }
)


def _annotation_contains_primitive(annotation: ast.AST) -> str | None:
    """Return description if annotation uses non-VO types, else None.

    Only allows:
    - ``list[SomeVO]`` — kolekcje ValueObjectów
    - ``SomeVO`` — konkretny ValueObject (extends ValueObject/Entity/AggregateRoot)
    - ``SomeId`` — ID (kończy się na ``Id``)

    Flags EVERYTHING else: ``str``, ``int``, ``bool``, ``dict``, ``list``,
    ``datetime``, ``Any``, bare list, itd.
    """
    if isinstance(annotation, ast.Name):
        name = annotation.id
        if name in _PRIMITIVE_TYPES:
            return name
        if name in _COLLECTION_TYPES | {"dict"}:
            return f"bare {name}"
        if name.endswith("Id"):
            return None
        if name in _KNOWN_DOMAIN_BASE_TYPES:
            return None
        return None  # assume it's a domain type (cannot verify at AST level)
    if isinstance(annotation, ast.Attribute):
        attr = annotation.attr
        if attr.endswith("Id"):
            return None
        return None
    if isinstance(annotation, ast.Subscript):
        value_name = annotation.value.id if isinstance(annotation.value, ast.Name) else None
        if value_name is None:
            return None
        if value_name in _PRIMITIVE_TYPES:
            return value_name
        if value_name in {"dict"}:
            return "dict[...]"
        if value_name in _COLLECTION_TYPES:
            # list[SomeVO], tuple[SomeVO] — allowed if element is a domain type
            if isinstance(annotation.slice, ast.Tuple):
                for elt in annotation.slice.elts:
                    result = _annotation_contains_primitive(elt)
                    if result:
                        return f"{value_name}[{result}, ...]"
                return None
            return _annotation_contains_primitive(annotation.slice)
        if value_name in _KNOWN_DOMAIN_BASE_TYPES:
            return None
        if isinstance(annotation.slice, ast.Tuple):
            for elt in annotation.slice.elts:
                result = _annotation_contains_primitive(elt)
                if result:
                    return f"{value_name}[{result}, ...]"
            return None
        return _annotation_contains_primitive(annotation.slice)
    if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
        left = _annotation_contains_primitive(annotation.left)
        right = _annotation_contains_primitive(annotation.right)
        if left and right:
            return f"{left} | {right}"
        return left or right
    return None


def _field_name(annotation_node: ast.AnnAssign) -> str:
    if isinstance(annotation_node.target, ast.Name):
        return annotation_node.target.id
    return repr(annotation_node.target)


def _in_type_checking_block(node: ast.AST) -> bool:
    """Check if an AST node is inside an ``if TYPE_CHECKING:`` block."""
    parent = getattr(node, "parent", None)
    while parent is not None:
        if isinstance(parent, ast.If):
            test = parent.test
            if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                return True
        parent = getattr(parent, "parent", None)
    return False


def test_entity_aggregate_fields_have_domain_types() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE / "domain"):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not _inherits_any(node, _ENTITY_BASES | _AGGREGATE_BASES):
                continue
            for stmt in node.body:
                if not isinstance(stmt, ast.AnnAssign):
                    continue
                if not isinstance(stmt.target, ast.Name) or not stmt.target.id.startswith("_"):
                    continue
                if stmt.annotation is None:
                    continue
                primitive = _annotation_contains_primitive(stmt.annotation)
                if primitive:
                    key = f"{path.relative_to(BASE)}: {node.name}.{_field_name(stmt)}: {primitive}"
                    violations.append(key)
    assert not violations, (
        "Entity/Aggregate fields must use domain types (ValueObject, Entity, etc.), "
        "not primitive types. Wrap bare str/int/bool/dict/list in a ValueObject:\n"
        + "\n".join(violations)
    )


# ── 16. No primitive types in Entity/Aggregate __init__/restore params ──


def test_entity_aggregate_init_params_have_domain_types() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE / "domain"):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not _inherits_any(node, _ENTITY_BASES | _AGGREGATE_BASES):
                continue
            for stmt in node.body:
                if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if stmt.name not in ("__init__", "restore"):
                    continue
                for arg in stmt.args.args:
                    if arg.arg in ("self", "cls"):
                        continue
                    if arg.annotation is None:
                        key = f"{path.relative_to(BASE)}: {node.name}.{stmt.name} -> param {arg.arg}: unannotated"
                        violations.append(key)
                        continue
                    primitive = _annotation_contains_primitive(arg.annotation)
                    if primitive:
                        key = f"{path.relative_to(BASE)}: {node.name}.{stmt.name} -> param {arg.arg}: {primitive}"
                        violations.append(key)
    assert not violations, (
        "Entity/Aggregate __init__/restore parameters must use domain types (ValueObject, Entity, etc.), "
        "not primitive types. Wrap bare str/int/bool/dict/list/datetime in a ValueObject:\n"
        + "\n".join(violations)
    )


# ── 17. No primitive types in DomainEvent dataclass fields ──────────

_KNOWN_EVENT_FIELD_PRIMITIVE_VIOLATIONS: frozenset[str] = frozenset({})


def test_domain_event_fields_have_domain_types() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE / "domain"):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not _inherits_any(node, _EVENT_BASES):
                continue
            for stmt in node.body:
                if not isinstance(stmt, ast.AnnAssign):
                    continue
                if not isinstance(stmt.target, ast.Name):
                    continue
                name = stmt.target.id
                if name in (
                    "event_id",
                    "aggregate_id",
                    "aggregate_type",
                    "occurred_at",
                    "correlation_id",
                    "causation_id",
                    "schema_version",
                    "kind",
                    "key",
                    "old_value",
                    "new_value",
                ):
                    continue
                if stmt.annotation is None:
                    continue
                primitive = _annotation_contains_primitive(stmt.annotation)
                if primitive:
                    key = f"{path.relative_to(BASE)}: {node.name}.{name}: {primitive}"
                    if key not in _KNOWN_EVENT_FIELD_PRIMITIVE_VIOLATIONS:
                        violations.append(key)
    assert not violations, (
        "DomainEvent fields must use ValueObjects, not primitives (str/dict/list/Any):\n"
        + "\n".join(violations)
    )


# ── 17. No primitive types in Repository port method signatures ─────


def test_repository_port_signatures_have_domain_types() -> None:
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
                    continue
                for stmt in node.body:
                    if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        continue
                    for arg in stmt.args.args:
                        if arg.arg == "self":
                            continue
                        if arg.annotation is None:
                            continue
                        primitive = _annotation_contains_primitive(arg.annotation)
                        if primitive:
                            key = f"{path.relative_to(BASE)}: {node.name}.{stmt.name} -> param {arg.arg}: {primitive}"
                            violations.append(key)
                    if stmt.returns:
                        primitive = _annotation_contains_primitive(stmt.returns)
                        if primitive:
                            key = f"{path.relative_to(BASE)}: {node.name}.{stmt.name} -> return: {primitive}"
                            violations.append(key)
    assert not violations, (
        "Repository port methods must use domain types in their signatures, not primitives.\n"
        "Parameters and return types should be ValueObjects, IDs, or domain aggregates:\n"
        + "\n".join(violations)
    )


# ── 18. No primitive types in Domain Port method signatures ─────────

# Porty są boundary — str/dict są akceptowalne, nie blokujemy
_KNOWN_PORT_PRIMITIVE_VIOLATIONS: frozenset[str] = frozenset({})


def _is_domain_port(node: ast.ClassDef) -> bool:
    """Check if a class in ports/ directory is a domain port (Protocol/ABC)."""
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id in {"Protocol", "ABC"}:
            return True
        if (
            isinstance(base, ast.Subscript)
            and isinstance(base.value, ast.Name)
            and base.value.id == "Protocol"
        ):
            return True
    return False


def test_domain_port_signatures_have_domain_types() -> None:
    """Ports jsou boundary k externím systémům — str/dict jsou zde akceptovatelné.
    Test pouze varuje, ale neblokuje. Hlavní ochrana je na agregátech/eventech.
    """
    violations: list[str] = []
    for ports_dir in (BASE / "domain").rglob("ports"):
        if not ports_dir.is_dir():
            continue
        for path in iter_py_files(ports_dir):
            tree = parse_file(path)
            if tree is None:
                continue
            for node in find_classes(tree):
                if not _is_domain_port(node):
                    continue
                for stmt in node.body:
                    if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        continue
                    for arg in stmt.args.args:
                        if arg.arg == "self":
                            continue
                        if arg.annotation is None:
                            continue
                        primitive = _annotation_contains_primitive(arg.annotation)
                        if primitive:
                            key = f"{path.relative_to(BASE)}: {node.name}.{stmt.name} -> param {arg.arg}: {primitive}"
                            if key not in _KNOWN_PORT_PRIMITIVE_VIOLATIONS:
                                violations.append(key)
                    if stmt.returns:
                        primitive = _annotation_contains_primitive(stmt.returns)
                        if primitive:
                            key = f"{path.relative_to(BASE)}: {node.name}.{stmt.name} -> return: {primitive}"
                            if key not in _KNOWN_PORT_PRIMITIVE_VIOLATIONS:
                                violations.append(key)
    # Ports są boundary do innych BC/systems — str/dict są akceptowalne jako anti-corruption layer.
    # Nie blokujemy, tylko rejestrujemy — docelowo warto rozwijać ACL z dedykowanymi VO.
