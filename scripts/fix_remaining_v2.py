#!/usr/bin/env python
"""Add remaining _delete/_update stubs + missing slots to all aggregates."""

from __future__ import annotations

import re
from pathlib import Path


def add_stub(content: str, method_name: str) -> str:
    if f"def {method_name}(" in content:
        return content
    stub = (
        f"\n    def {method_name}(self) -> None:\n"
        f'        raise NotImplementedError("{method_name}() not yet implemented")\n'
    )
    lines = content.split("\n")
    insert_at = len(lines) - 1
    for i, line in enumerate(lines):
        if "@property" in line and i > 5:
            insert_at = i
            break
    lines.insert(insert_at, stub)
    return "\n".join(lines)


def fix_file(path: Path) -> bool:
    content = path.read_text("utf-8")
    orig = content

    content = add_stub(content, "_delete")
    content = add_stub(content, "_update")

    # Add _created_at/_updated_at to slots if missing
    for field in ('"_created_at"', '"_updated_at"'):
        if field not in content:
            content = re.sub(
                r"(__slots__\s*=\s*\()",
                f"\\1\n        {field},",
                content,
                count=1,
            )

    if content != orig:
        path.write_text(content, "utf-8")
        return True
    return False


def main() -> None:
    fixed = 0
    for path in sorted(Path("shell/domain").rglob("**/aggregates/**/*.py")):
        if any(
            p in path.parts
            for p in ("events", "exceptions", "value_objects", "repositories", "__init__")
        ):
            continue
        if "AggregateRoot" not in path.read_text("utf-8"):
            continue
        if fix_file(path):
            print(f"FIXED: {path}")
            fixed += 1
    print(f"\nFixed {fixed} files")


if __name__ == "__main__":
    main()
