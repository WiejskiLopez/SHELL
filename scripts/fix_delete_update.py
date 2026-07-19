#!/usr/bin/env python
"""Implement _delete() and _update() in all aggregates + create event files."""

from __future__ import annotations

import ast
import re
from pathlib import Path

BASE = Path("shell/domain")

EVENT_TEMPLATE_DELETED = """from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from {id_module} import {id_type}
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class {name}DeletedEvent(DomainEvent):
    {name_lower}_id: {id_type}

    @classmethod
    def now(cls, {name_lower}_id: {id_type}, now: CreatedAt) -> "{name}DeletedEvent":
        return cls(occurred_at=now, {name_lower}_id={name_lower}_id)
"""

EVENT_TEMPLATE_UPDATED = """from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from {id_module} import {id_type}
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class {name}UpdatedEvent(DomainEvent):
    {name_lower}_id: {id_type}

    @classmethod
    def now(cls, {name_lower}_id: {id_type}, now: CreatedAt) -> "{name}UpdatedEvent":
        return cls(occurred_at=now, {name_lower}_id={name_lower}_id)
"""


def get_aggregate_name(content: str) -> str | None:
    m = re.search(r"class (\w+)\(.*AggregateRoot", content)
    return m.group(1) if m else None


def get_id_type(content: str) -> str | None:
    m = re.search(r"class \w+\(.*AggregateRoot\[(\w+)\]", content)
    return m.group(1) if m else None


def find_id_module(agg_name: str, id_type: str) -> str | None:
    """Find the module path for an ID type under the aggregate's directory."""
    for f in sorted(BASE.rglob(f"**/{agg_name.lower()}/**/value_objects/*.py")):
        content = f.read_text("utf-8")
        if f"class {id_type}" in content:
            rel = f.relative_to(BASE)
            parts = list(rel.parts)
            return f"shell.domain.{'.'.join(parts[:-1])}.{parts[-1].replace('.py', '')}"
    return None


def ensure_event_files(agg_dir: Path, name: str, id_type: str, id_module: str) -> None:
    event_dir = agg_dir / "events"
    event_dir.mkdir(exist_ok=True)

    for event_type, template in [
        ("Deleted", EVENT_TEMPLATE_DELETED),
        ("Updated", EVENT_TEMPLATE_UPDATED),
    ]:
        ef = event_dir / f"{name.lower()}_{event_type.lower()}_event.py"
        if ef.exists():
            continue
        content = template.format(
            name=name,
            name_lower=name.lower(),
            id_type=id_type,
            id_module=id_module,
        )
        ef.write_text(content, "utf-8")
        print(f"  EVENT: {ef}")


def add_import(content: str, imp: str) -> str:
    if imp in content:
        return content
    lines = content.split("\n")
    insert_at = 0
    for i, l in enumerate(lines):
        if l.startswith("from shell.") and "TYPE_CHECKING" not in l:
            insert_at = i + 1
    lines.insert(insert_at, imp)
    return "\n".join(lines)


def fix_aggregate(path: Path) -> bool:
    content = path.read_text("utf-8")
    orig = content

    name = get_aggregate_name(content)
    if not name:
        return False

    id_type = get_id_type(content)
    if not id_type:
        return False

    id_module = find_id_module(name, id_type)
    if not id_module:
        # Fallback: guess from path
        parts = path.relative_to(BASE).parts
        bc_name = parts[0]
        agg_name = parts[2] if len(parts) > 2 else name.lower()
        id_module = f"shell.domain.{bc_name}.aggregates.{agg_name}.value_objects.{id_type}"
        print(f"  GUESSED ID module for {name}: {id_module}")

    # Create event files
    ensure_event_files(path.parent, name, id_type, id_module)

    # Add event imports
    deleted_import = f"from {'.'.join(path.relative_to(BASE).parent.as_posix().replace('.py', '').split('/'))}.events.{name.lower()}_deleted_event import {name}DeletedEvent"
    deleted_import = deleted_import.replace("\\", "/")
    updated_import = f"from {'.'.join(path.relative_to(BASE).parent.as_posix().replace('.py', '').split('/'))}.events.{name.lower()}_updated_event import {name}UpdatedEvent"
    updated_import = updated_import.replace("\\", "/")

    content = add_import(content, deleted_import)
    content = add_import(content, updated_import)
    content = add_import(
        content, "from shell.platform.domain.value_objects.deleted_at import DeletedAt"
    )
    content = add_import(
        content, "from shell.platform.domain.value_objects.updated_at import UpdatedAt"
    )

    # Check _delete()
    if re.search(r"def _delete\(self", content):
        # Replace NotImplementedError stub with real implementation
        content = re.sub(
            r"    def _delete\(self\) -> None:\n        raise NotImplementedError\(\"_delete\(\) not yet implemented\"\)\n?",
            f"    def _delete(self, now: DeletedAt) -> None:\n"
            f"        self._deleted_at = now\n"
            f"        self._updated_at = UpdatedAt.from_datetime(now.value)\n"
            f"        self.append_event(\n"
            f"            {name}DeletedEvent.now(\n"
            f"                {name.lower()}_id=self._id,\n"
            f"                now=CreatedAt.from_datetime(now.value),\n"
            f"            )\n"
            f"        )",
            content,
        )
    elif "def _delete" not in content:
        # Add _delete method
        content = add_method(
            content,
            f"    def _delete(self, now: DeletedAt) -> None:\n"
            f"        self._deleted_at = now\n"
            f"        self._updated_at = UpdatedAt.from_datetime(now.value)\n"
            f"        self.append_event(\n"
            f"            {name}DeletedEvent.now(\n"
            f"                {name.lower()}_id=self._id,\n"
            f"                now=CreatedAt.from_datetime(now.value),\n"
            f"            )\n"
            f"        )",
        )

    # Check _update()
    if re.search(r"def _update\(self", content):
        content = re.sub(
            r"    def _update\(self\) -> None:\n        raise NotImplementedError\(\"_update\(\) not yet implemented\"\)\n?",
            f"    def _update(self, now: UpdatedAt) -> None:\n"
            f"        self._updated_at = now\n"
            f"        self.append_event(\n"
            f"            {name}UpdatedEvent.now(\n"
            f"                {name.lower()}_id=self._id,\n"
            f"                now=CreatedAt.from_datetime(now.value),\n"
            f"            )\n"
            f"        )",
            content,
        )
    elif "def _update" not in content:
        content = add_method(
            content,
            f"    def _update(self, now: UpdatedAt) -> None:\n"
            f"        self._updated_at = now\n"
            f"        self.append_event(\n"
            f"            {name}UpdatedEvent.now(\n"
            f"                {name.lower()}_id=self._id,\n"
            f"                now=CreatedAt.from_datetime(now.value),\n"
            f"            )\n"
            f"        )",
        )

    if content != orig:
        path.write_text(content, "utf-8")
        return True
    return False


def add_method(content: str, method: str) -> str:
    """Add a method before the first @property."""
    lines = content.split("\n")
    insert_at = len(lines)
    for i, l in enumerate(lines):
        if "@property" in l and i > 5:
            insert_at = i
            break
    lines.insert(insert_at, method)
    return "\n".join(lines)


def main() -> None:
    fixed = 0
    for path in sorted(BASE.rglob("**/aggregates/**/*.py")):
        if any(
            p in path.parts
            for p in ("events", "exceptions", "value_objects", "repositories", "__init__")
        ):
            continue
        if "AggregateRoot" not in path.read_text("utf-8"):
            continue
        if fix_aggregate(path):
            print(f"FIXED: {path}")
            fixed += 1

    print(f"\nFixed {fixed} aggregates")


if __name__ == "__main__":
    main()
