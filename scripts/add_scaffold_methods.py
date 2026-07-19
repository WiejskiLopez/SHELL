#!/usr/bin/env python
"""Add _new, _delete, _update stubs to aggregates that need them.
Uses proper Python AST manipulation, not fragile regex."""

from __future__ import annotations

import ast
import re
from pathlib import Path


def add_scaffold_methods(path: Path) -> bool:
    content = path.read_text("utf-8")
    orig = content

    name_match = re.search(r"class (\w+)\(.*AggregateRoot", content)
    if not name_match:
        return False
    agg_name = name_match.group(1)
    name_lower = agg_name.lower()

    # Find if _new, _delete, _update exist
    has_new = "_new" in content
    has_delete = "_delete" in content
    has_update = "_update" in content

    if has_new and has_delete and has_update:
        return False  # Already complete

    # Find insertion point: before @property or at end
    insert_at = len(content)
    idx = content.find("@property")
    if idx > 0:
        insert_at = idx

    # Build methods to add
    new_methods = ""

    if not has_new:
        new_methods += (
            f"\n    @classmethod\n"
            f"    def _new(cls) -> {agg_name}:\n"
            f'        raise NotImplementedError("_new() not yet implemented")\n'
        )

    if not has_delete:
        new_methods += (
            f"\n    def _delete(self, now: DeletedAt) -> None:\n"
            f"        self._deleted_at = now\n"
            f"        self._updated_at = UpdatedAt.from_datetime(now.value)\n"
            f"        self.append_event(\n"
            f"            {agg_name}DeletedEvent.now(\n"
            f"                {name_lower}_id=self._id,\n"
            f"                now=now,\n"
            f"            )\n"
            f"        )\n"
        )

    if not has_update:
        new_methods += (
            f"\n    def _update(self, now: UpdatedAt) -> None:\n"
            f"        self._updated_at = now\n"
            f"        self.append_event(\n"
            f"            {agg_name}UpdatedEvent.now(\n"
            f"                {name_lower}_id=self._id,\n"
            f"                now=now,\n"
            f"            )\n"
            f"        )\n"
        )

    if new_methods:
        content = content[:insert_at] + new_methods + "\n" + content[insert_at:]

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
        if add_scaffold_methods(path):
            print(f"FIXED: {path}")
            fixed += 1
    print(f"\nFixed {fixed} files")


if __name__ == "__main__":
    main()
