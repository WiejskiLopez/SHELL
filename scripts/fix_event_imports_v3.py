#!/usr/bin/env python
"""Fix event file TYPE_CHECKING imports - use snake_case module paths."""
from pathlib import Path
import re


def fix_event_imports() -> None:
    count = 0
    for f in sorted(Path("shell/domain").rglob("**/events/*.py")):
        if f.name == "__init__.py":
            continue
        content = f.read_text("utf-8")
        orig = content

        lines = content.split("\n")
        new_lines = []
        for line in lines:
            # Match: from ...value_objects.CamelCaseId import (
            # Or: from ...value_objects.CamelCaseId import CamelCaseId
            m = re.match(
                r"(\s*from shell\.domain\..*?\.value_objects\.)([A-Z]\w+Id)( import.*)",
                line,
            )
            if m:
                prefix = m.group(1)
                full_type = m.group(2)  # e.g. TaskExecutionId
                suffix = m.group(3)
                # Convert TaskExecutionId -> task_execution_id
                snake = re.sub(r"([A-Z])", r"_\1", full_type).lower().lstrip("_")
                new_line = f"{prefix}{snake}{suffix}"
                new_lines.append(new_line)
            else:
                new_lines.append(line)

        content = "\n".join(new_lines)

        if content != orig:
            f.write_text(content, "utf-8")
            count += 1

    print(f"Fixed {count} event files")


if __name__ == "__main__":
    fix_event_imports()
