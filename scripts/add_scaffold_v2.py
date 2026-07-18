#!/usr/bin/env python
"""Add _new(), _delete(), _update() to all aggregates safely."""
from __future__ import annotations

import re
from pathlib import Path


def add_scaffold(path: Path) -> bool:
    content = path.read_text("utf-8")
    orig = content

    name_match = re.search(r"class (\w+)\(.*AggregateRoot", content)
    if not name_match:
        return False
    name = name_match.group(1)

    # Ensure imported modules
    imports_needed = []
    if "DeletedAt" in content and "from shell.platform.domain.value_objects.deleted_at import DeletedAt" not in content:
        imports_needed.append("from shell.platform.domain.value_objects.deleted_at import DeletedAt")
    if "UpdatedAt" in content and "from shell.platform.domain.value_objects.updated_at import UpdatedAt" not in content:
        imports_needed.append("from shell.platform.domain.value_objects.updated_at import UpdatedAt")

    if imports_needed:
        content = content.replace(
            "if TYPE_CHECKING:",
            "\n".join(imports_needed) + "\n\nif TYPE_CHECKING:",
            1,
        )

    methods = []

    # Add _new as wrapper for existing new/create/open
    if "def _new(" not in content:
        factory_name = None
        for fn in ["new", "create", "open"]:
            if re.search(rf"    @classmethod\n    def {fn}\(", content):
                factory_name = fn
                break
        if factory_name:
            methods.append(
                f"\n    @classmethod\n"
                f"    def _new(cls, *args: object, **kwargs: object) -> {name}:\n"
                f"        return cls.{factory_name}(*args, **kwargs)\n"
            )

    # Add _delete
    if "def _delete(" not in content:
        methods.append(
            f"\n    def _delete(self, now: DeletedAt) -> None:\n"
            f"        self._deleted_at = now\n"
            f"        self._updated_at = UpdatedAt.from_datetime(now.value)\n"
            f"        self.append_event(\n"
            f"            {name}DeletedEvent.now(\n"
            f"                {name.lower()}_id=self._id,\n"
            f"                now=now,\n"
            f"            )\n"
            f"        )\n"
        )

    # Add _update
    if "def _update(" not in content:
        methods.append(
            f"\n    def _update(self, now: UpdatedAt) -> None:\n"
            f"        self._updated_at = now\n"
            f"        self.append_event(\n"
            f"            {name}UpdatedEvent.now(\n"
            f"                {name.lower()}_id=self._id,\n"
            f"                now=now,\n"
            f"            )\n"
            f"        )\n"
        )

    if methods:
        # Insert before @property or at end
        idx = content.find("@property")
        if idx < 0:
            idx = len(content)
        content = content[:idx] + "".join(methods) + "\n" + content[idx:]

    if content != orig:
        path.write_text(content, "utf-8")
        return True
    return False


def main() -> None:
    fixed = 0
    for path in sorted(Path("shell/domain").rglob("**/aggregates/**/*.py")):
        if any(p in path.parts for p in ("events", "exceptions", "value_objects", "repositories", "__init__")):
            continue
        if "AggregateRoot" not in path.read_text("utf-8"):
            continue
        if add_scaffold(path):
            print(f"FIXED: {path}")
            fixed += 1
    print(f"\nFixed {fixed} aggregates")


if __name__ == "__main__":
    main()
