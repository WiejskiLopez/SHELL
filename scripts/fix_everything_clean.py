#!/usr/bin/env python
"""Single comprehensive fix: _delete/_update + event imports + DomainError + cleanup."""
from __future__ import annotations

import re
from pathlib import Path

BASE = Path("shell/domain")
EVENT_E_IMPORT = "from shell.platform.domain.value_objects.error_description import ErrorDescription"


def fix_aggregate(path: Path) -> bool:
    content = path.read_text("utf-8")
    orig = content

    name_match = re.search(r"class (\w+)\(.*AggregateRoot", content)
    if not name_match:
        return False
    name = name_match.group(1)

    # 1. Remove all broken/malformed imports
    content = re.sub(r"^    \w+DeletedEvent,\n\s*\)\n", "", content, flags=re.MULTILINE)
    content = re.sub(r"^    \w+UpdatedEvent,\n\s*\)\n", "", content, flags=re.MULTILINE)
    content = re.sub(r"from definition\.aggregates.*\n", "", content)
    content = re.sub(r"from execution\.aggregates.*\n", "", content)
    content = re.sub(r"from scheduling\.aggregates.*\n", "", content)
    content = re.sub(r"from session\.aggregates.*\n", "", content)
    content = re.sub(r"from user\.aggregates.*\n", "", content)
    content = re.sub(r"from project\.aggregates.*\n", "", content)
    content = re.sub(r"from messaging\.aggregates.*\n", "", content)

    # 2. Remove NotImplementedError _new stubs
    content = re.sub(
        r"    @classmethod\n    def _new\(cls\) -> \w+:\n        raise NotImplementedError\(\"_new\(\) not yet implemented\"\)\n?",
        "",
        content,
    )

    # 3. Add DomainError import if DomainError is used
    if "DomainError" in content and "from shell.platform.domain.exceptions.domain_error import DomainError" not in content:
        content = content.replace(
            "from __future__ import annotations",
            "from __future__ import annotations\nfrom shell.platform.domain.exceptions.domain_error import DomainError",
        )

    # 4. Replace raise ValueError with raise DomainError
    content = re.sub(r"raise ValueError\(([^)]*)\)", r"raise DomainError(\1)", content)

    # 5. Add proper event imports
    parts = path.relative_to(BASE).parts
    parent_module = "shell.domain." + ".".join(p for p in parts[:-1])
    events_module = parent_module + ".events"

    for event_type in ("DeletedEvent", "UpdatedEvent"):
        event_name = name + event_type
        event_file = name.lower() + "_" + event_type.lower()
        imp = f"from {events_module}.{event_file} import {event_name}"
        if event_name in content and imp not in content:
            content = content.replace("if TYPE_CHECKING:", imp + "\n\nif TYPE_CHECKING:", 1)

    # 6. Replace NotImplementedError _delete/_update stubs with real implementations
    stub_del = f"    def _delete(self) -> None:\n        raise NotImplementedError(\"_delete() not yet implemented\")"
    stub_upd = f"    def _update(self) -> None:\n        raise NotImplementedError(\"_update() not yet implemented\")"

    real_del = (
        f"    def _delete(self, now: DeletedAt) -> None:\n"
        f"        self._deleted_at = now\n"
        f"        self._updated_at = UpdatedAt.from_datetime(now.value)\n"
        f"        self.append_event(\n"
        f"            {name}DeletedEvent.now(\n"
        f"                {name.lower()}_id=self._id,\n"
        f"                now=now,\n"
        f"            )\n"
        f"        )"
    )
    real_upd = (
        f"    def _update(self, now: UpdatedAt) -> None:\n"
        f"        self._updated_at = now\n"
        f"        self.append_event(\n"
        f"            {name}UpdatedEvent.now(\n"
        f"                {name.lower()}_id=self._id,\n"
        f"                now=now,\n"
        f"            )\n"
        f"        )"
    )

    if stub_del in content:
        content = content.replace(stub_del, real_del, 1)
    if stub_upd in content:
        content = content.replace(stub_upd, real_upd, 1)

    # 7. Cleanup: remove empty lines at top + duplicate blank lines
    content = re.sub(r"\n{3,}", "\n\n", content)

    if content != orig:
        path.write_text(content, "utf-8")
        return True
    return False


def main() -> None:
    fixed = 0
    for path in sorted(BASE.rglob("**/aggregates/**/*.py")):
        if any(p in path.parts for p in ("events", "exceptions", "value_objects", "repositories", "__init__")):
            continue
        if "AggregateRoot" not in path.read_text("utf-8"):
            continue
        if fix_aggregate(path):
            print(f"FIXED: {path}")
            fixed += 1
    print(f"\nFixed {fixed} files")


if __name__ == "__main__":
    main()
