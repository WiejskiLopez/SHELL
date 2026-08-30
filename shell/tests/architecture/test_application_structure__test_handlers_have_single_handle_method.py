"""Koncept: reguła architektoniczna dotycząca application structure: test handlers have single handle method.

Reguła: test sprawdza kontrakt architektoniczny application structure: test handlers have single handle method.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    find_classes,
    iter_named_dirs,
    iter_py_files,
    parse_file,
    public_method_names,
)

_KNOWN_HANDLER_EXCEPTIONS: frozenset[str] = frozenset({})
_KNOWN_QUERIES_NOT_FROZEN: frozenset[str] = frozenset({})


def test_handlers_have_single_handle_method() -> None:
    violations: list[str] = []
    for handler_kind in ("command_handlers", "query_handlers", "event_handlers"):
        for handler_dir in iter_named_dirs("application", handler_kind):
            for path in iter_py_files(handler_dir):
                tree = parse_file(path)
                if tree is None:
                    continue
                for node in find_classes(tree):
                    if not node.name.endswith("Handler"):
                        continue
                    pub_methods = public_method_names(node)
                    handle_methods = [m for m in pub_methods if m == "handle"]
                    if len(handle_methods) != 1:
                        key = f"{path.relative_to(BASE)}: class {node.name}"
                        if key not in _KNOWN_HANDLER_EXCEPTIONS:
                            violations.append(key)
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_handlers_have_single_handle_method",
        "warunek zapisany w asercji musi być spełniony",
        "Handlers must have exactly one public method named `handle`:\n" + "\n".join(violations),
    )
