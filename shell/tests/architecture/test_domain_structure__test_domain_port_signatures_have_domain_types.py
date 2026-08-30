"""Koncept: reguła architektoniczna dotycząca domain structure: test domain port signatures have domain types.

Reguła: test sprawdza kontrakt architektoniczny domain structure: test domain port signatures have domain types.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

import ast

from _arch_helpers import (
    BASE,
    find_classes,
    iter_named_dirs,
    iter_py_files,
    parse_file,
)

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
    {"ValueObject", "Entity", "AggregateRoot", "DomainEvent", "Protocol", "ABC", "Self", "type"}
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
        return None
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


_KNOWN_PORT_PRIMITIVE_VIOLATIONS: frozenset[str] = frozenset({})


def _is_domain_port(node: ast.ClassDef) -> bool:
    """Check if a class in ports/ directory is a domain port (Protocol/ABC)."""
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id in {"Protocol", "ABC"}:
            return True
        if (
            isinstance(base, ast.Subscript)
            and isinstance(base.value, ast.Name)
            and (base.value.id == "Protocol")
        ):
            return True
    return False


def test_domain_port_signatures_have_domain_types() -> None:
    """Ports jsou boundary k externím systémům — str/dict jsou zde akceptovatelné.
    Test pouze varuje, ale neblokuje. Hlavní ochrana je na agregátech/eventech.
    """
    violations: list[str] = []
    for ports_dir in iter_named_dirs("domain", "ports"):
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
