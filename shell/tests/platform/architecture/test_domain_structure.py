from __future__ import annotations

import ast
import pathlib

from _arch_helpers import (
    BASE,
    all_method_names,
    extends_any_base,
    find_classes,
    has_method,
    has_public_setter,
    has_slots,
    is_frozen_dataclass,
    iter_py_files,
    parse_file,
    public_method_names,
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

_KNOWN_VO_NO_SLOTS: frozenset[str] = frozenset({
    "domain/execution/value_objects/graph_execution_definition.py: class GraphNodeExecutionDefinition",
    "domain/execution/value_objects/graph_execution_definition.py: class GraphExecutionDefinition",
    "domain/execution/value_objects/task_execution_body.py: class TaskExecutionBody",
    "domain/execution/aggregates/workflow/value_objects/workflow_state_input.py: class WorkflowStateInput",
    "domain/execution/aggregates/workflow/value_objects/workflow_state_output.py: class WorkflowStateOutput",
    "domain/execution/aggregates/session/value_objects/session_state_input.py: class SessionStateInput",
    "domain/execution/aggregates/session/value_objects/session_state_output.py: class SessionStateOutput",
})


def _is_strenum(node: ast.ClassDef) -> bool:
    """Check if a class extends StrEnum (which can't have slots=True)."""
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id == "StrEnum":
            return True
    return False


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
        "ValueObjects must be @dataclass(frozen=True, slots=True):\n"
        + "\n".join(violations)
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
        if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name) and dec.func.id == "dataclass":
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
    assert not violations, (
        "Entities/AggregateRoots must define __slots__:\n"
        + "\n".join(violations)
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
    assert not violations, (
        "Entities/AggregateRoots must not have public setters:\n"
        + "\n".join(violations)
    )


# ── 5. Init params assigned to private attrs with _ prefix ────────


_KNOWN_PUBLIC_INIT_ATTRS: frozenset[str] = frozenset({
    # Definition BC entities use public attrs pattern (non-aggregate entities with @dataclass-like init)
    "domain/definition/entities/graph_definition.py: GraphDefinition.__init__ assigns to public 'name'",
    "domain/definition/entities/graph_definition.py: GraphDefinition.__init__ assigns to public 'purpose'",
    "domain/definition/entities/graph_definition.py: GraphDefinition.__init__ assigns to public 'graph_node_definitions'",
    "domain/definition/entities/graph_definition.py: GraphDefinition.__init__ assigns to public 'transition_definitions'",
    "domain/definition/entities/graph_node_definition.py: GraphNodeDefinition.__init__ assigns to public 'position'",
    "domain/definition/entities/graph_node_definition.py: GraphNodeDefinition.__init__ assigns to public 'mode'",
    "domain/definition/entities/graph_node_definition.py: GraphNodeDefinition.__init__ assigns to public 'role'",
    "domain/definition/entities/graph_node_transition_definition.py: GraphNodeTransitionDefinition.__init__ assigns to public 'graph_definition_id'",
    "domain/definition/entities/runner_config.py: RunnerConfig.__init__ assigns to public 'package_name'",
    "domain/definition/aggregates/rag_document/rag_document.py: RagDocument.__init__ assigns to public 'source_uri'",
    "domain/definition/aggregates/rag_document/entities/rag_chunk.py: RagChunk.__init__ assigns to public 'document_id'",
    "domain/user/aggregates/user/user.py: User.__init__ assigns to public 'identity'",
    "domain/scheduling/aggregates/scheduler_definition/scheduler_definition.py: SchedulerDefinition.__init__ assigns to public 'name'",
    "domain/scheduling/aggregates/scheduler_execution/scheduler_execution.py: SchedulerExecution.__init__ assigns to public 'scheduler_definition_id'",
    "domain/scheduling/aggregates/scheduler_job/scheduler_job.py: SchedulerJob.__init__ assigns to public 'scheduler_execution_id'",
    "domain/projekt/aggregates/project/project.py: Project.__init__ assigns to public 'name'",
    "domain/execution/aggregates/envelope/envelope.py: Envelope.__init__ assigns to public 'task_execution_id'",
    "domain/execution/aggregates/session/session.py: Session.__init__ assigns to public 'task_execution_id'",
    "domain/execution/aggregates/agent_config_execution/agent_config_execution.py: AgentConfigExecution.__init__ assigns to public 'config'",
    "domain/execution/aggregates/agent_execution/agent_execution.py: AgentExecution.__init__ assigns to public 'id'",
})


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
                        if isinstance(line, ast.Attribute):
                            if isinstance(line.value, ast.Name) and line.value.id == "self":
                                if not line.attr.startswith("_"):
                                    key = f"{path.relative_to(BASE)}: {node.name}.__init__ assigns to public {line.attr!r}"
                                    if key not in _KNOWN_PUBLIC_INIT_ATTRS:
                                        violations.append(key)
    assert not violations, (
        "Entity/AggregateRoot __init__ must assign to private attributes with _ prefix:\n"
        + "\n".join(violations)
    )


# ── 6. Domain Event: @dataclass(frozen=True), extends DomainEvent ──

_KNOWN_NON_EVENT_DOMAIN_CLASSES: frozenset[str] = frozenset({
    "domain/platform/base/__init__.py: class Entity",
    "domain/platform/base/__init__.py: class AggregateRoot",
    "domain/platform/base/__init__.py: class TId",
})


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
    assert not violations, (
        "DomainEvents must be @dataclass(frozen=True):\n"
        + "\n".join(violations)
    )


# ── 7. Domain Event has from_payload() ────────────────────────────


def test_domain_events_have_from_payload() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE / "domain"):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not _inherits_any(node, _EVENT_BASES):
                continue
            if not has_method(node, "from_payload"):
                key = f"{path.relative_to(BASE)}: class {node.name}"
                if key not in _KNOWN_NON_EVENT_DOMAIN_CLASSES:
                    violations.append(key)
    assert not violations, (
        "DomainEvents must define from_payload() classmethod:\n"
        + "\n".join(violations)
    )


# ── 8. Mutating methods in aggregates append_event() ──────────────

_KNOWN_NO_EVENT_EMIT: frozenset[str] = frozenset({
    # Scheduling & user BC aggregates follow different event pattern
    "domain/scheduling/aggregates/scheduler_definition/scheduler_definition.py: SchedulerDefinition.matches_trigger",
    "domain/execution/aggregates/agent_config_execution/agent_config_execution.py: AgentConfigExecution.update_config",
    "domain/execution/aggregates/agent_execution/agent_execution.py: AgentExecution.for_node",
    "domain/execution/aggregates/agent_execution/agent_execution.py: AgentExecution.add_skill",
    "domain/execution/aggregates/envelope/envelope.py: Envelope.archive",
    "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.absorb_child_results",
    "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.mark_verifying",
    "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.create_main_round",
    "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.create_sub_graph",
    "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.set_spawn_expected_node_count",
    "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.resume_from_ready",
    "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.add_skill",
    "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.add_state_input",
    "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.add_state_output",
    "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.add_transition",
    "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.add_graph_node_execution_id",
    "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.get_outgoing_transitions",
    "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.get_incoming_transitions",
    "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.increment_loop_counter",
    "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.from_graph_definition",
    "domain/execution/aggregates/graph_execution_state_input/graph_execution_state_input.py: GraphExecutionStateInput.get",
    "domain/execution/aggregates/graph_execution_state_input/graph_execution_state_input.py: GraphExecutionStateInput.patch",
    "domain/execution/aggregates/graph_execution_state_input/graph_execution_state_input.py: GraphExecutionStateInput.clear",
    "domain/execution/aggregates/graph_execution_state_input/graph_execution_state_input.py: GraphExecutionStateInput.snapshot",
    "domain/execution/aggregates/graph_execution_state_input/graph_execution_state_input.py: GraphExecutionStateInput.supersede",
    "domain/execution/aggregates/graph_execution_state_output/graph_execution_state_output.py: GraphExecutionStateOutput.get",
    "domain/execution/aggregates/graph_execution_state_output/graph_execution_state_output.py: GraphExecutionStateOutput.patch",
    "domain/execution/aggregates/graph_execution_state_output/graph_execution_state_output.py: GraphExecutionStateOutput.clear",
    "domain/execution/aggregates/graph_execution_state_output/graph_execution_state_output.py: GraphExecutionStateOutput.merge",
    "domain/execution/aggregates/graph_execution_state_output/graph_execution_state_output.py: GraphExecutionStateOutput.snapshot",
    "domain/execution/aggregates/graph_execution_state_output/graph_execution_state_output.py: GraphExecutionStateOutput.supersede",
    "domain/execution/aggregates/graph_node_execution/graph_node_execution.py: GraphNodeExecution.add_output_state",
    "domain/execution/aggregates/graph_node_execution/graph_node_execution.py: GraphNodeExecution.add_input_state",
    "domain/execution/aggregates/graph_node_execution/graph_node_execution.py: GraphNodeExecution.get_latest_input_state",
    "domain/execution/aggregates/graph_node_execution/graph_node_execution.py: GraphNodeExecution.get_latest_output_state",
    "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.create_sequence",
    "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.create_conditional",
    "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.create_loop",
    "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.create_spawn_subgraph",
    "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.create_error_handler",
    "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.create_timeout",
    "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.create_default",
    "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.skip",
    "domain/execution/aggregates/task_execution/task_execution.py: TaskExecution.increment_cycle",
    "domain/execution/aggregates/task_execution/task_execution.py: TaskExecution.add_skill",
    "domain/execution/aggregates/task_execution/task_execution.py: TaskExecution.add_state_input",
    "domain/execution/aggregates/task_execution/task_execution.py: TaskExecution.add_state_output",
    "domain/execution/aggregates/task_execution/task_execution.py: TaskExecution.rename",
    "domain/execution/aggregates/task_execution/task_execution.py: TaskExecution.execute_in_workflow",
    "domain/execution/aggregates/task_execution/task_execution.py: TaskExecution.prepare_workspace",
    "domain/execution/aggregates/task_execution_state_input/task_execution_state_input.py: TaskExecutionStateInput.supersede",
    "domain/execution/aggregates/task_execution_state_output/task_execution_state_output.py: TaskExecutionStateOutput.supersede",
})


def _is_property(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for dec in node.decorator_list:
        if isinstance(dec, ast.Attribute) and dec.attr == "getter":
            return True
        if isinstance(dec, ast.Name) and dec.id == "property":
            return True
    return False


def test_mutating_methods_emit_events() -> None:
    violations: list[str] = []
    _NON_MUTATING = frozenset({"__init__", "restore", "pull_events", "to_dict", "new", "create", "generate"})
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
        "Public mutating methods in aggregates must call append_event():\n"
        + "\n".join(violations)
    )


# ── 9. Guard clauses at the start of mutating methods ──────────────

_KNOWN_NO_GUARD: frozenset[str] = frozenset({
    "domain/scheduling/aggregates/scheduler_definition/scheduler_definition.py: SchedulerDefinition.matches_trigger",
    "domain/scheduling/aggregates/scheduler_execution/scheduler_execution.py: SchedulerExecution.start",
    "domain/scheduling/aggregates/scheduler_execution/scheduler_execution.py: SchedulerExecution.complete",
    "domain/scheduling/aggregates/scheduler_execution/scheduler_execution.py: SchedulerExecution.fail",
    "domain/scheduling/aggregates/scheduler_execution/scheduler_execution.py: SchedulerExecution.skip",
    "domain/execution/aggregates/agent_config_execution/agent_config_execution.py: AgentConfigExecution.update_config",
    "domain/execution/aggregates/agent_execution/agent_execution.py: AgentExecution.for_node",
    "domain/execution/aggregates/agent_execution/agent_execution.py: AgentExecution.add_skill",
    "domain/execution/aggregates/envelope/envelope.py: Envelope.transition_stage",
    "domain/execution/aggregates/envelope/envelope.py: Envelope.deliver_to",
    "domain/execution/aggregates/envelope/envelope.py: Envelope.archive",
    "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.create_main_round",
    "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.set_spawn_expected_node_count",
    "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.add_skill",
    "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.add_state_input",
    "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.add_state_output",
    "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.add_transition",
    "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.add_graph_node_execution_id",
    "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.get_outgoing_transitions",
    "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.get_incoming_transitions",
    "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.increment_loop_counter",
    "domain/execution/aggregates/graph_execution/graph_execution.py: GraphExecution.from_graph_definition",
    "domain/execution/aggregates/graph_execution_state_input/graph_execution_state_input.py: GraphExecutionStateInput.update",
    "domain/execution/aggregates/graph_execution_state_input/graph_execution_state_input.py: GraphExecutionStateInput.get",
    "domain/execution/aggregates/graph_execution_state_input/graph_execution_state_input.py: GraphExecutionStateInput.delete",
    "domain/execution/aggregates/graph_execution_state_input/graph_execution_state_input.py: GraphExecutionStateInput.patch",
    "domain/execution/aggregates/graph_execution_state_input/graph_execution_state_input.py: GraphExecutionStateInput.clear",
    "domain/execution/aggregates/graph_execution_state_input/graph_execution_state_input.py: GraphExecutionStateInput.snapshot",
    "domain/execution/aggregates/graph_execution_state_input/graph_execution_state_input.py: GraphExecutionStateInput.supersede",
    "domain/execution/aggregates/graph_execution_state_output/graph_execution_state_output.py: GraphExecutionStateOutput.update",
    "domain/execution/aggregates/graph_execution_state_output/graph_execution_state_output.py: GraphExecutionStateOutput.get",
    "domain/execution/aggregates/graph_execution_state_output/graph_execution_state_output.py: GraphExecutionStateOutput.delete",
    "domain/execution/aggregates/graph_execution_state_output/graph_execution_state_output.py: GraphExecutionStateOutput.patch",
    "domain/execution/aggregates/graph_execution_state_output/graph_execution_state_output.py: GraphExecutionStateOutput.clear",
    "domain/execution/aggregates/graph_execution_state_output/graph_execution_state_output.py: GraphExecutionStateOutput.merge",
    "domain/execution/aggregates/graph_execution_state_output/graph_execution_state_output.py: GraphExecutionStateOutput.snapshot",
    "domain/execution/aggregates/graph_execution_state_output/graph_execution_state_output.py: GraphExecutionStateOutput.supersede",
    "domain/execution/aggregates/graph_node_execution/graph_node_execution.py: GraphNodeExecution.add_output_state",
    "domain/execution/aggregates/graph_node_execution/graph_node_execution.py: GraphNodeExecution.add_input_state",
    "domain/execution/aggregates/graph_node_execution/graph_node_execution.py: GraphNodeExecution.get_latest_input_state",
    "domain/execution/aggregates/graph_node_execution/graph_node_execution.py: GraphNodeExecution.get_latest_output_state",
    "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.create_sequence",
    "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.create_conditional",
    "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.create_loop",
    "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.create_spawn_subgraph",
    "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.create_error_handler",
    "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.create_timeout",
    "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution.create_default",
    "domain/execution/aggregates/session/session.py: Session.open",
    "domain/execution/aggregates/session/session.py: Session.add_skill",
    "domain/execution/aggregates/task_execution/task_execution.py: TaskExecution.increment_cycle",
    "domain/execution/aggregates/task_execution/task_execution.py: TaskExecution.add_skill",
    "domain/execution/aggregates/task_execution/task_execution.py: TaskExecution.add_state_input",
    "domain/execution/aggregates/task_execution/task_execution.py: TaskExecution.add_state_output",
    "domain/execution/aggregates/task_execution/task_execution.py: TaskExecution.rename",
    "domain/execution/aggregates/task_execution/task_execution.py: TaskExecution.execute_in_workflow",
    "domain/execution/aggregates/task_execution/task_execution.py: TaskExecution.prepare_workspace",
    "domain/execution/aggregates/task_execution_state_input/task_execution_state_input.py: TaskExecutionStateInput.supersede",
    "domain/execution/aggregates/task_execution_state_output/task_execution_state_output.py: TaskExecutionStateOutput.supersede",
    "domain/execution/aggregates/workflow/workflow.py: Workflow.add_skill",
    "domain/execution/aggregates/workflow/workflow.py: Workflow.add_state_input",
    "domain/execution/aggregates/workflow/workflow.py: Workflow.add_state_output",
    "domain/definition/entities/graph_definition.py: GraphDefinition.add_graph_node_definition",
    "domain/definition/entities/graph_definition.py: GraphDefinition.remove_graph_node_definition",
    "domain/definition/entities/graph_definition.py: GraphDefinition.get_graph_node_definition",
    "domain/definition/entities/graph_definition.py: GraphDefinition.add_transition_definition",
    "domain/platform/base/aggregate_root.py: AggregateRoot.append_event",
})


def test_mutating_methods_have_guard() -> None:
    violations: list[str] = []
    _NON_MUTATING = frozenset({"__init__", "restore", "pull_events", "to_dict", "new", "create", "generate", "of"})
    for path in iter_py_files(BASE / "domain"):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not _inherits_any(node, _AGGREGATE_BASES | _ENTITY_BASES):
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

_KNOWN_PAST_EVENTS: frozenset[str] = frozenset({
    "domain/platform/events/domain_event.py: class DomainEvent",
})


_KNOWN_PAST_EVENTS: frozenset[str] = frozenset({
    "domain/platform/events/domain_event.py: class DomainEvent",
    "domain/execution/aggregates/graph_node_transition_execution/events/graph_node_transition_execution_timed_out_event.py: class GraphNodeTransitionExecutionTimedOutEvent",
    "domain/execution/aggregates/graph_node_transition_execution/events/graph_node_transition_execution_transition_taken_event.py: class GraphNodeTransitionExecutionTransitionTakenEvent",
    "domain/execution/aggregates/graph_node_execution/events/graph_node_execution_timed_out_event.py: class GraphNodeExecutionTimedOutEvent",
    "domain/execution/aggregates/graph_execution/events/graph_execution_ready_event.py: class GraphExecutionReadyEvent",
})


def test_domain_event_past_tense_naming() -> None:
    import re
    violations: list[str] = []
    pattern = re.compile(r".*(ed|ted|led|ned|ged|ked|zed|hed|ped|bed|ved|wed|ched|gged|pped|tted|lled|rred|nned|mmed)$", re.IGNORECASE)
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
    assert not violations, (
        "Specifications must extend Specification[T]:\n"
        + "\n".join(violations)
    )


# ── 12. Collections returned as copies ─────────────────────────────

_KNOWN_COLLECTION_RETURN_ISSUES: frozenset[str] = frozenset({
})


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
    return bool(src.startswith("self._") and any(
        keyword in src for keyword in ["list", "dict", "set", "tuple", "collections"]
    ))


def _is_copy_pattern(node: ast.AST) -> bool:
    src = ast.unparse(node)
    return ".copy()" in src or "list(" in src or "tuple(" in src or "[:]" in src


# ── 13. Domain Service is stateless ────────────────────────────────


_KNOWN_SVC_STATEFUL: frozenset[str] = frozenset({
    "domain/execution/services/sub_graph_execution_service.py: class SubGraphExecutionService has state: ['_clock', '_definition_provider', '_governance', '_id_generator', '_logger', '_observer', '_security', '_unit_of_work', '_versioning']",
})


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
                        if isinstance(line, ast.Attribute):
                            if isinstance(line.value, ast.Name) and line.value.id == "self":
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


_KNOWN_ID_ONLY_VIOLATIONS: frozenset[str] = frozenset({
    "domain/execution/aggregates/graph_node_transition_execution/graph_node_transition_execution.py: GraphNodeTransitionExecution._target_node_execution_id: GraphNodeExecutionId | None",
    "domain/execution/aggregates/workflow/workflow.py: Workflow._status: WorkflowStatus",
    "domain/execution/aggregates/workflow/workflow.py: Workflow._skills: list[WorkflowSkill]",
    "domain/execution/aggregates/workflow/workflow.py: Workflow._state_inputs: list[WorkflowStateInput]",
    "domain/execution/aggregates/workflow/workflow.py: Workflow._state_outputs: list[WorkflowStateOutput]",
})


def test_aggregate_references_by_id_only() -> None:
    violations: list[str] = []
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
                    if not ann_src.endswith("Id") and "ValueObject" not in ann_src:
                        for _agg_name in ["AggregateRoot", "Entity", "Workflow", "TaskExecution",
                                          "GraphExecution", "GraphNodeExecution"]:
                            if _agg_name in ann_src:
                                key = f"{path.relative_to(BASE).as_posix()}: {node.name}.{ast.unparse(stmt.target)}: {ann_src}"
                                if key not in _KNOWN_ID_ONLY_VIOLATIONS:
                                    violations.append(key)
    assert not violations, (
        "Aggregates should reference other aggregates by ID only (not by object reference):\n"
        + "\n".join(violations)
    )
