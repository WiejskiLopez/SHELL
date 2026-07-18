#!/usr/bin/env python
"""Add *CreatedEvent emission to aggregates that lack it."""
from __future__ import annotations

import re
from pathlib import Path


def ensure_event_file(agg_dir: Path, name: str, id_type: str) -> bool:
    """Create a {Name}CreatedEvent file if it doesn't exist."""
    event_dir = agg_dir / "events"
    event_dir.mkdir(exist_ok=True)
    event_file = event_dir / f"{name.lower()}_created_event.py"
    if event_file.exists():
        return False

    init_file = event_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text("from __future__ import annotations\n", encoding="utf-8")

    content = f'''from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from {id_type} import {id_type.rsplit(".", 1)[-1]}
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class {name}CreatedEvent(DomainEvent):
    {name.lower()}_id: {id_type.rsplit(".", 1)[-1]}

    @classmethod
    def now(cls, {name.lower()}_id: {id_type.rsplit(".", 1)[-1]}, now: CreatedAt) -> "{name}CreatedEvent":
        return cls(occurred_at=now, {name.lower()}_id={name.lower()}_id)
'''
    event_file.write_text(content, encoding="utf-8")
    return True


def add_event_to_new(content: str, name: str, id_var: str, agg_file: Path) -> str:
    """Add append_event call to _new() method."""
    if "CreatedEvent" in content:
        return content

    event_module = f"{name}CreatedEvent"

    # Find _new method body and add append_event before return
    pattern = r'(def _new\([^)]*\)[^:]*:\n(?:.*\n)*?)(\s+)(return instance)'
    m = re.search(pattern, content)
    if not m:
        return content

    indent = m.group(2)
    event_call = (
        f"{indent}instance.append_event(\n"
        f"{indent}    {event_module}.now(\n"
        f"{indent}        {name.lower()}_id=instance.id,\n"
        f"{indent}        now=now,\n"
        f"{indent}    )\n"
        f"{indent})"
    )
    content = content.replace(m.group(0), f"{m.group(1)}{event_call}\n\n{m.group(2)}{m.group(3)}")

    # Add import
    import_line = f"from shell.domain.{agg_file.relative_to(Path('shell/domain')).parent.as_posix().replace('/', '.')}.events.{name.lower()}_created_event import {event_module}"
    import_line = import_line.replace("\\", "/")

    if import_line not in content:
        # Find last regular import
        lines = content.split("\n")
        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith("from shell.") and "TYPE_CHECKING" not in line:
                insert_at = i + 1
        lines.insert(insert_at, import_line)
        content = "\n".join(lines)

    return content


def main() -> None:
    base = Path("shell/domain")
    # These need events added
    targets = [
        ("shell/domain/scheduling/aggregates/scheduler_definition/scheduler_definition.py", "SchedulerDefinition"),
        ("shell/domain/scheduling/aggregates/scheduler_job/scheduler_job.py", "SchedulerJob"),
        ("shell/domain/execution/aggregates/agent_execution/agent_execution.py", "AgentExecution"),
        ("shell/domain/execution/aggregates/agent_skill_execution/agent_skill_execution.py", "AgentSkillExecution"),
        ("shell/domain/execution/aggregates/node_link_execution/node_link_execution.py", "NodeLinkExecution"),
        ("shell/domain/definition/aggregates/node_link_definition/node_link_definition.py", "NodeLinkDefinition"),
    ]

    for rel_path, name in targets:
        agg_path = Path(rel_path)
        if not agg_path.exists():
            print(f"NOT FOUND: {agg_path}")
            continue

        content = agg_path.read_text("utf-8")
        agg_dir = agg_path.parent

        # Determine ID type from file
        id_match = re.search(r"class (\w+)\(AggregateRoot\[(\w+)\]", content)
        if not id_match:
            print(f"NO ID TYPE: {agg_path}")
            continue

        agg_name = id_match.group(1)
        id_type = id_match.group(2)

        # Find id_type module path
        id_file = list(Path("shell/domain").rglob(f"**/{id_type.lower()}.py"))
        id_module = None
        for f in id_file:
            if f"value_objects" in str(f):
                rel = f.relative_to(base)
                id_module = f"shell.domain.{rel.parent.as_posix().replace('/', '.')}.{id_type}"
                break
        if not id_module:
            print(f"NO ID MODULE for {id_type}: {agg_path}")
            id_module = f"shell.domain.{agg_name.lower()}.aggregates.{agg_name.lower()}.value_objects.{id_type}"

        print(f"\nProcessing {agg_name} ({agg_path})")
        print(f"  ID: {id_type} -> {id_module}")

        if ensure_event_file(agg_dir, agg_name, id_module):
            print(f"  Created event file")

        new_content = add_event_to_new(content, agg_name, id_module, agg_path)
        if new_content != content:
            agg_path.write_text(new_content, "utf-8")
            print(f"  Updated _new() with event emission")
        else:
            print(f"  No changes needed")


if __name__ == "__main__":
    main()
