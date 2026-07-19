#!/usr/bin/env python
"""Fix event file TYPE_CHECKING imports."""

from pathlib import Path
import re

count = 0
for f in sorted(Path("shell/domain").rglob("**/events/*.py")):
    if f.name == "__init__.py":
        continue
    c = f.read_text("utf-8")
    orig = c

    # Fix: from shell.domain.x.value_objects.CamelCaseId import CamelCaseId
    # To: from shell.domain.x.value_objects.snake_case_id import CamelCaseId
    c = re.sub(
        r"(from shell\.domain\..*?\.value_objects\.)([A-Z]\w+Id)( import \2)",
        lambda m: (
            m.group(1) + re.sub(r"([A-Z])", r"_\1", m.group(2)).lower().lstrip("_") + m.group(3)
        ),
        c,
    )

    if c != orig:
        f.write_text(c, encoding="utf-8")
        count += 1

print(f"Fixed {count} event files")
