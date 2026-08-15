"""Architecture rules for test ownership boundaries."""

from __future__ import annotations

from _arch_helpers import BASE, get_imports, iter_py_files


def test_platform_tests_do_not_import_definition_service() -> None:
    platform_tests = BASE / "tests" / "platform"
    violations: list[str] = []
    for path in iter_py_files(platform_tests):
        for imported in get_imports(path):
            if imported == "shell.definition_service" or imported.startswith(
                "shell.definition_service."
            ):
                violations.append(f"{path.relative_to(BASE)}: imports {imported!r}")

    assert not violations, "Platform tests must not import definition_service:\n" + "\n".join(
        violations
    )
