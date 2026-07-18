#!/usr/bin/env python
"""Fix event file imports - wrong module paths."""
import re
from pathlib import Path


def fix_event_imports() -> None:
    for f in sorted(Path("shell/domain").rglob("**/events/*.py")):
        if f.name == "__init__.py":
            continue
        c = f.read_text("utf-8")
        orig = c

        # Find lines like: from shell.domain.xxx.value_objects.GraphDefinitionId import (
        lines = c.split("\n")
        new_lines = []
        for i, line in enumerate(lines):
            # Match: from shell.domain.x.value_objects.GraphDefinitionId import (
            m = re.match(
                r"(\s*from shell\.domain\..*\.value_objects\.)([A-Z]\w+Id)( import)",
                line,
            )
            if m:
                prefix = m.group(1)
                full_type = m.group(2)  # e.g. GraphDefinitionId
                suffix = m.group(3)
                # Convert CamelCase to snake_case
                # GraphDefinitionId -> graph_definition_id
                snake = re.sub(r"([A-Z])", r"_\1", full_type).lower().lstrip("_")
                new_line = f"{prefix}{snake}{suffix}"
                new_lines.append(new_line)
            else:
                new_lines.append(line)

        c = "\n".join(new_lines)

        if c != orig:
            f.write_text(c, encoding="utf-8")
            print(f"FIXED: {f}")


if __name__ == "__main__":
    fix_event_imports()
