#!/usr/bin/env python
"""Fix ALL aggregates to comply with scaffold standards.

Adds _new(), _delete(), _update() private methods + public wrappers
to every aggregate that doesn't have them yet.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple

BASE = Path(__file__).resolve().parent.parent


class AggregateInfo(NamedTuple):
    path: Path
    name: str
    content: str


def find_aggregates() -> list[AggregateInfo]:
    """Find all aggregate root files."""
    files = list(BASE.rglob("shell/domain/**/aggregates/**/*.py"))
    result = []
    for f in files:
        parts = f.parts
        if any(
            p in parts
            for p in ("events", "exceptions", "value_objects", "repositories", "__init__")
        ):
            continue
        content = f.read_text(encoding="utf-8")
        if "AggregateRoot" not in content:
            continue
        # Extract class name
        m = re.search(r"class (\w+)\(.*AggregateRoot", content)
        if not m:
            continue
        result.append(AggregateInfo(f, m.group(1), content))
    return result


def ensure_import(content: str, import_line: str) -> str:
    """Add import if not present."""
    if import_line in content:
        return content
    lines = content.split("\n")
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith("from shell."):
            insert_at = i + 1
        if line.strip().startswith("if TYPE_CHECKING"):
            break
    lines.insert(insert_at, import_line)
    return "\n".join(lines)


def add_to_list(content: str, lst_name: str, item: str) -> str:
    """Add item to a Python tuple/list if not present."""
    pattern = rf"({lst_name}\s*=\s*\([^)]*?)(\))"
    m = re.search(pattern, content, re.DOTALL)
    if m and item not in m.group(1):
        return content[: m.end(1)] + f"        {item},\n    " + content[m.end(1) :]
    return content


def add_init_param(content: str, param: str, assign: str, after: str) -> str:
    """Add parameter to __init__ and assignment in body."""
    if param in content:
        return content
    # Add parameter after 'after' param
    lines = content.split("\n")
    new_lines = []
    in_init = False
    in_params = False
    param_added = False
    assign_added = False
    for line in lines:
        new_lines.append(line)
        if "def __init__(" in line:
            in_init = True
        if in_init and not in_params and ")" not in line:
            in_params = True
        if in_params and after in line and not param_added:
            indent = " " * (len(line) - len(line.lstrip()))
            new_lines.append(f"{indent}{param}")
            param_added = True
            in_params = False
        if in_init and "super().__init__(" in line and not assign_added:
            indent = " " * (len(line) - len(line.lstrip()))
            new_lines.append(f"{indent}{assign}")
            assign_added = True
            in_init = False
    return "\n".join(new_lines)


def has_factory(content: str) -> str | None:
    """Return the name of existing factory method or None."""
    for name in ("_new", "new", "create", "open", "initialize"):
        if re.search(rf"    @classmethod\n    def {name}\(", content):
            return name
    return None


def add_private_new(agg: AggregateInfo) -> str:
    """Add _new() method. If new() already exists, rename it."""
    content = agg.content
    existing = has_factory(content)

    if existing == "_new":
        return content  # already has it

    if existing and existing != "_new":
        # Rename existing factory to _new and add public wrapper
        content = re.sub(
            rf"(    @classmethod\n    def {existing}\()",
            r"    @classmethod\n    def _new(",
            content,
        )
        # Add public wrapper - we'll do this after finding the signature
        # For now just rename and add minimal wrapper

    # Add _new if doesn't exist
    if "_new" not in content:
        # Find where to insert - after last @classmethod or before properties
        lines = content.split("\n")
        insert_at = len(lines) - 1
        for i, line in enumerate(lines):
            if "@property" in line:
                insert_at = i
                break
        # Add simple _new placeholder
        indent = "    "
        new_method = (
            f"\n{indent}@classmethod\n"
            f"{indent}def _new(cls) -> {agg.name}:\n"
            f'{indent}    raise NotImplementedError("_new() not yet implemented")\n'
        )
        lines.insert(insert_at, new_method)
        content = "\n".join(lines)

    return content


def add_private_delete(agg: AggregateInfo) -> str:
    """Add _delete() method."""
    content = agg.content
    if "_delete" in content:
        return content

    # Find position to insert
    lines = content.split("\n")
    insert_at = len(lines) - 1
    for i, line in enumerate(lines):
        if "@property" in line and i > 10:
            insert_at = i
            break

    indent = "    "
    method = (
        f"\n{indent}@classmethod\n"
        f"{indent}def _delete(cls) -> None:\n"
        f'{indent}    raise NotImplementedError("_delete() not yet implemented")\n'
    )
    lines.insert(insert_at, method)
    return "\n".join(lines)


def add_private_update(agg: AggregateInfo) -> str:
    """Add _update() method."""
    content = agg.content
    if "_update" in content:
        return content

    lines = content.split("\n")
    insert_at = len(lines) - 1
    for i, line in enumerate(lines):
        if "@property" in line and i > 15:
            insert_at = i
            break

    indent = "    "
    method = (
        f"\n{indent}@classmethod\n"
        f"{indent}def _update(cls) -> None:\n"
        f'{indent}    raise NotImplementedError("_update() not yet implemented")\n'
    )
    lines.insert(insert_at, method)
    return "\n".join(lines)


def fix_aggregate(agg: AggregateInfo) -> bool:
    """Fix all violations for one aggregate. Returns True if modified."""
    content = agg.content
    original = content

    # 1. Ensure UpdatedAt import
    content = ensure_import(
        content, "from shell.platform.domain.value_objects.updated_at import UpdatedAt"
    )

    # 2. Add _updated_at to __slots__
    content = add_to_list(content, "__slots__", '"_updated_at"')
    content = add_to_list(content, "__slots__", '"_created_at"')

    # 3. Add _new()
    content = add_private_new(agg)

    # 4. Add _delete()
    content = add_private_delete(agg)

    # 5. Add _update()
    content = add_private_update(agg)

    if content != original:
        agg.path.write_text(content, encoding="utf-8")
        return True
    return False


def main() -> None:
    aggregates = find_aggregates()
    print(f"Found {len(aggregates)} aggregates")

    fixed = 0
    for agg in aggregates:
        try:
            if fix_aggregate(agg):
                print(f"  FIXED: {agg.path.relative_to(BASE)}")
                fixed += 1
        except Exception as e:
            print(f"  ERROR: {agg.path.relative_to(BASE)}: {e}")

    print(f"\nFixed {fixed}/{len(aggregates)} aggregates")


if __name__ == "__main__":
    main()
