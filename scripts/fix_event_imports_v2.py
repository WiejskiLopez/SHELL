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
    lines = c.split("\n")
    new_lines = []
    for line in lines:
        m = re.match(
            r"(\s*from shell\.domain\..*?\.value_objects\.)([A-Z]\w+Id)( import \2)",
            line,
        )
        if m:
            prefix = m.group(1)
            full_type = m.group(2)
            suffix = m.group(3)
            # Convert CamelCaseId to snake_case_id
            snake = re.sub(r"([A-Z])", r"_\1", full_type).lower().lstrip("_")
            new_line = f"{prefix}{snake}{suffix}"
            new_lines.append(new_line)
        else:
            new_lines.append(line)
    
    c = "\n".join(new_lines)
    
    if c != orig:
        f.write_text(c, encoding="utf-8")
        count += 1

print(f"Fixed {count} event files")
