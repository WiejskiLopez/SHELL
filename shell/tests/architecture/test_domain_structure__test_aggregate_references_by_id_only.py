"""Koncept: reguła architektoniczna dotycząca domain structure: test aggregate references by id only.

Reguła: test sprawdza kontrakt architektoniczny domain structure: test aggregate references by id only.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""
from __future__ import annotations

import ast
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Iterator
from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    extends_any_base,
    find_classes,
    iter_py_files,
    parse_file,
)

_VO_BASES = {'ValueObject'}
_ENTITY_BASES = {'Entity'}
_AGGREGATE_BASES = {'AggregateRoot'}
_EVENT_BASES = {'DomainEvent'}
_DOMAIN_BASES = _VO_BASES | _ENTITY_BASES | _AGGREGATE_BASES | _EVENT_BASES
_SPEC_BASES = {'Specification'}

def _inherits_any(node: ast.ClassDef, bases: set[str]) -> bool:
    return extends_any_base(node, bases)
_KNOWN_VO_NO_SLOTS: frozenset[str] = frozenset({})

def _is_strenum(node: ast.ClassDef) -> bool:
    """Check if a class extends StrEnum (which can't have slots=True)."""
    return any(isinstance(base, ast.Name) and base.id == 'StrEnum' for base in node.bases)

def _has_dataclass_decorator(node: ast.ClassDef) -> bool:
    for dec in node.decorator_list:
        if isinstance(dec, ast.Name) and dec.id == 'dataclass':
            return True
        if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name) and (dec.func.id == 'dataclass'):
            return True
    return False
_KNOWN_PUBLIC_INIT_ATTRS: frozenset[str] = frozenset({})
_KNOWN_NON_EVENT_DOMAIN_CLASSES: frozenset[str] = frozenset({})
_EVENT_FIELD_ALLOWLIST: frozenset[str] = frozenset({'occurred_at'})
_KNOWN_NO_EVENT_EMIT: frozenset[str] = frozenset({'TaskExecution.rename', 'User.enable', 'User.disable', 'NodeExecution.start', 'NodeExecution.complete', 'NodeExecution.fail', 'NodeExecution.retry', 'NodeExecution.timeout', 'TaskExecution.start', 'TaskExecution.complete', 'TaskExecution.fail', 'TaskExecution.timeout', 'TaskExecution.exhaust', 'Workflow.start_at', 'Workflow.finish', 'Workflow.fail', 'Workflow.abort', 'Workflow.pause', 'Workflow.resume', 'NodeExecution.mark_deleted'})

def _is_property(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for dec in node.decorator_list:
        if isinstance(dec, ast.Attribute) and dec.attr == 'getter':
            return True
        if isinstance(dec, ast.Name) and dec.id == 'property':
            return True
    return False

def _delegates_to_emitting_transition(stmt: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Public mutating methods may delegate to _change()/_delete()/_new() which emit events."""
    for call in ast.walk(stmt):
        if isinstance(call, ast.Call):
            func_src = ast.unparse(call.func)
            if func_src in ('self._change', 'self._delete', 'self._new'):
                return True
    return False
_KNOWN_NO_GUARD: frozenset[str] = frozenset({'TaskExecution.rename', 'Project.change', 'Project.delete'})

def _is_raise_body(node: ast.If) -> bool:

    def _has_raise(stmts: list[ast.stmt]) -> bool:
        return any(isinstance(s, ast.Raise) for s in stmts)
    return _has_raise(node.body) or _has_raise(node.orelse)
_KNOWN_PAST_EVENTS: frozenset[str] = frozenset({})
_KNOWN_COLLECTION_RETURN_ISSUES: frozenset[str] = frozenset({})

def _is_collection_type(node: ast.AST) -> bool:
    src = ast.unparse(node)
    return bool(src.startswith('self._') and any(keyword in src for keyword in ['list', 'dict', 'set', 'tuple', 'collections']))

def _is_copy_pattern(node: ast.AST) -> bool:
    src = ast.unparse(node)
    return '.copy()' in src or 'list(' in src or 'tuple(' in src or ('[:]' in src)
_KNOWN_SVC_STATEFUL: frozenset[str] = frozenset({})
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
_PRIMITIVE_TYPES: frozenset[str] = frozenset({'str', 'int', 'bool', 'float', 'bytes', 'Any', 'datetime', 'Decimal', 'Path', 'date', 'time', 'timedelta', 'UUID'})
_COLLECTION_TYPES: frozenset[str] = frozenset({'dict', 'list', 'set', 'tuple', 'frozenset'})
_KNOWN_DOMAIN_BASE_TYPES: frozenset[str] = frozenset({'ValueObject', 'Entity', 'AggregateRoot', 'DomainEvent', 'Protocol', 'ABC', 'Self', 'type'})

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
        if name in _COLLECTION_TYPES | {'dict'}:
            return f'bare {name}'
        if name.endswith('Id'):
            return None
        if name in _KNOWN_DOMAIN_BASE_TYPES:
            return None
        return None
    if isinstance(annotation, ast.Attribute):
        attr = annotation.attr
        if attr.endswith('Id'):
            return None
        return None
    if isinstance(annotation, ast.Subscript):
        value_name = annotation.value.id if isinstance(annotation.value, ast.Name) else None
        if value_name is None:
            return None
        if value_name in _PRIMITIVE_TYPES:
            return value_name
        if value_name in {'dict'}:
            return 'dict[...]'
        if value_name in _COLLECTION_TYPES:
            if isinstance(annotation.slice, ast.Tuple):
                for elt in annotation.slice.elts:
                    result = _annotation_contains_primitive(elt)
                    if result:
                        return f'{value_name}[{result}, ...]'
                return None
            return _annotation_contains_primitive(annotation.slice)
        if value_name in _KNOWN_DOMAIN_BASE_TYPES:
            return None
        if isinstance(annotation.slice, ast.Tuple):
            for elt in annotation.slice.elts:
                result = _annotation_contains_primitive(elt)
                if result:
                    return f'{value_name}[{result}, ...]'
            return None
        return _annotation_contains_primitive(annotation.slice)
    if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
        left = _annotation_contains_primitive(annotation.left)
        right = _annotation_contains_primitive(annotation.right)
        if left and right:
            return f'{left} | {right}'
        return left or right
    return None

def _field_name(annotation_node: ast.AnnAssign) -> str:
    if isinstance(annotation_node.target, ast.Name):
        return annotation_node.target.id
    return repr(annotation_node.target)

def _in_type_checking_block(node: ast.AST) -> bool:
    """Check if an AST node is inside an ``if TYPE_CHECKING:`` block."""
    parent = getattr(node, 'parent', None)
    while parent is not None:
        if isinstance(parent, ast.If):
            test = parent.test
            if isinstance(test, ast.Name) and test.id == 'TYPE_CHECKING':
                return True
        parent = getattr(parent, 'parent', None)
    return False
_KNOWN_FIELD_PRIMITIVE_VIOLATIONS: frozenset[str] = frozenset({})
_KNOWN_INIT_PARAM_VIOLATIONS: frozenset[str] = frozenset({})
_KNOWN_EVENT_FIELD_PRIMITIVE_VIOLATIONS: frozenset[str] = frozenset({})
_KNOWN_PORT_PRIMITIVE_VIOLATIONS: frozenset[str] = frozenset({})

def _is_domain_port(node: ast.ClassDef) -> bool:
    """Check if a class in ports/ directory is a domain port (Protocol/ABC)."""
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id in {'Protocol', 'ABC'}:
            return True
        if isinstance(base, ast.Subscript) and isinstance(base.value, ast.Name) and (base.value.id == 'Protocol'):
            return True
    return False
_ENTITY_ID_BASES = {'EntityId'}
_VO_BASES_SET = {'ValueObject'}
_KNOWN_ID_NOT_ENTITY_ID: frozenset[str] = frozenset({})
_KNOWN_IDREF_DUPLICATES: frozenset[str] = frozenset({})

def _extract_bc(path: pathlib.Path) -> str | None:
    rel = path.relative_to(BASE).as_posix()
    parts = rel.split('/')
    if len(parts) >= 2 and parts[0] == 'domain':
        return parts[1]
    return None
_AGGREGATE_FACTORY_METHODS = frozenset({'create', 'new'})
_NON_FACTORY_AGGREGATES: frozenset[str] = frozenset({})

def _iter_domain_files() -> Iterator[pathlib.Path]:
    """Iterate all real domain directories across bounded contexts and platform.

    After the monolith split, domain code lives per-service (shell/<svc>/domain) plus
    shell/platform/domain, not shell/domain. Using _iter_domain_files()
    would silently match nothing and disable every domain architecture test.
    """
    for service_dir in (BASE / 'platform', *BASE.glob('*_service')):
        domain_dir = service_dir / 'domain'
        yield from iter_py_files(domain_dir)

def _classmethod_source(node: ast.ClassDef, method_name: str) -> ast.FunctionDef | None:
    for stmt in node.body:
        if isinstance(stmt, ast.FunctionDef) and stmt.name == method_name and any(isinstance(dec, ast.Name) and dec.id == 'classmethod' for dec in stmt.decorator_list):
            return stmt
    return None

def _calls_new(stmt: ast.FunctionDef) -> bool:
    for call in ast.walk(stmt):
        if isinstance(call, ast.Call):
            func_src = ast.unparse(call.func)
            if func_src in ('_new', 'cls._new', 'cls.new') or func_src.endswith('._new'):
                return True
    return False

def _emits_created_event(stmt: ast.FunctionDef) -> bool:
    for call in ast.walk(stmt):
        if isinstance(call, ast.Call):
            func_src = ast.unparse(call.func)
            if func_src == 'append_event' or func_src.endswith('.append_event'):
                if len(call.args) > 0 and 'CreatedEvent' in ast.unparse(call.args[0]):
                    return True
                if call.keywords and any('CreatedEvent' in ast.unparse(kw.value) for kw in call.keywords):
                    return True
    return False

def test_aggregate_references_by_id_only() -> None:
    violations: list[str] = []
    _AGGREGATE_CLASS_NAMES = frozenset({'Workflow', 'TaskExecution', 'GraphExecution', 'NodeExecution', 'WorkflowState'})
    _KNOWN_INTERNAL_ENTITY_PREFIXES: set[str] = set()
    for path in _iter_domain_files():
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if not _inherits_any(node, _AGGREGATE_BASES):
                continue
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and stmt.annotation:
                    ann_src = ast.unparse(stmt.annotation)
                    if ann_src.endswith('Id'):
                        continue
                    type_names = _extract_type_names(stmt.annotation)
                    pure_agg_names = [t for t in type_names if t in _AGGREGATE_CLASS_NAMES and (not any(t.startswith(prefix) for prefix in _KNOWN_INTERNAL_ENTITY_PREFIXES))]
                    if pure_agg_names:
                        key = f'{path.relative_to(BASE).as_posix()}: {node.name}.{ast.unparse(stmt.target)}: {ann_src}'
                        if key not in _KNOWN_ID_ONLY_VIOLATIONS:
                            violations.append(key)
    assert not violations, architecture_assertion_message('reguła testowana przez test_aggregate_references_by_id_only', 'warunek zapisany w asercji musi być spełniony', 'Aggregates should reference other aggregates by ID only (not by object reference):\n' + '\n'.join(violations))
