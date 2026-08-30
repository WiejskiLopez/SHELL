"""Koncept: reguła architektoniczna dotycząca naming conventions: test handler classes end with handler.

Reguła: test sprawdza kontrakt architektoniczny naming conventions: test handler classes end with handler.

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
)


def test_handler_classes_end_with_handler() -> None:
    violations: list[str] = []
    for handlers_name in ("command_handlers", "query_handlers", "event_handlers"):
        for handler_dir in iter_named_dirs("application", handlers_name):
            for path in iter_py_files(handler_dir):
                tree = parse_file(path)
                if tree is None:
                    continue
                for node in find_classes(tree):
                    if not node.name.endswith("Handler"):
                        violations.append(f"{path.relative_to(BASE)}: class {node.name}")
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_handler_classes_end_with_handler",
        "warunek zapisany w asercji musi być spełniony",
        "Handler classes must end with 'Handler':\n" + "\n".join(violations),
    )
