#!/usr/bin/env python
"""Fix all remaining aggregates: _new with events + timestamps."""
from pathlib import Path

# Create event files
events_data = {
    ("shell/domain/definition/aggregates/node_link_definition/events/node_link_definition_created_event.py",
     "NodeLinkDefinition", "NodeLinkDefinitionId",
     "shell.domain.definition.aggregates.node_link_definition.value_objects.node_link_definition_id"),
    ("shell/domain/definition/aggregates/runner_config/events/runner_config_created_event.py",
     "RunnerConfig", "RunnerConfigId",
     "shell.domain.definition.aggregates.runner_config.value_objects.runner_config_id"),
    ("shell/domain/scheduling/aggregates/scheduler_job/events/scheduler_job_created_event.py",
     "SchedulerJob", "SchedulerExecutionId",
     "shell.domain.scheduling.aggregates.scheduler_execution.value_objects.scheduler_execution_id"),
}

for epath, name, id_type, id_module in events_data:
    p = Path(epath)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        f'''from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from {id_module} import {id_type}
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class {name}CreatedEvent(DomainEvent):
    {name.lower()}_id: {id_type}

    @classmethod
    def now(cls, {name.lower()}_id: {id_type}, now: CreatedAt) -> "{name}CreatedEvent":
        return cls(occurred_at=now, {name.lower()}_id={name.lower()}_id)
''')
    print(f"EVENT: {epath}")

# Now read and fix each aggregate
import re

fixes = [
    {
        "path": "shell/domain/definition/aggregates/node_link_definition/node_link_definition.py",
        "event_name": "NodeLinkDefinitionCreatedEvent",
        "event_import": "from shell.domain.definition.aggregates.node_link_definition.events.node_link_definition_created_event import NodeLinkDefinitionCreatedEvent",
        "add_now": True,
        "add_timestamps": True,
    },
    {
        "path": "shell/domain/definition/aggregates/runner_config/runner_config.py",
        "event_name": "RunnerConfigCreatedEvent",
        "event_import": "from shell.domain.definition.aggregates.runner_config.events.runner_config_created_event import RunnerConfigCreatedEvent",
        "add_now": True,
        "add_timestamps": False,
    },
    {
        "path": "shell/domain/scheduling/aggregates/scheduler_job/scheduler_job.py",
        "event_name": "SchedulerJobCreatedEvent",
        "event_import": "from shell.domain.scheduling.aggregates.scheduler_job.events.scheduler_job_created_event import SchedulerJobCreatedEvent",
        "add_now": True,
        "add_timestamps": False,
    },
]

for f in fixes:
    p = Path(f["path"])
    content = p.read_text("utf-8")
    orig = content

    # Add event import
    content = content.replace(
        "from shell.platform.domain.base.aggregate_root import AggregateRoot",
        f"from shell.platform.domain.base.aggregate_root import AggregateRoot\n{f['event_import']}",
    )

    # Remove stubs
    content = re.sub(r"    def _(?:new|delete|update)\(self\) -> None:\n        raise NotImplementedError\(\"_[a-z]+\(\) not yet implemented\"\)\n?", "", content)
    content = re.sub(r"\n{3,}", "\n\n", content)

    # Rename factory to _new
    content = re.sub(r"    def (?:create|new)\(", "    def _new(", content)

    # Find the _new method and modify it
    # Change `return cls(` to `instance = cls(` and add event + return instance
    _new_match = re.search(r"(def _new\([^)]*\)[^:]*:\n(?:        .*\n)*?)(return cls\()", content)
    if _new_match:
        prefix = _new_match.group(1)
        content = content.replace(
            _new_match.group(0),
            prefix + "instance = cls("
        )
        # Now add event emission before next method
        event_call = f"""        instance.append_event(
            {f['event_name']}.now(
                {p.parent.name.lower()}_id=instance.id,
                now=now,
            )
        )
        return instance"""
        content = content.replace(
            "        )\n\n    @classmethod",
            f"        )\n{event_call}\n\n    @classmethod",
        )

    # Add back public wrapper
    if f"    def create(" not in content and f"    def new(" not in content:
        param_match = re.search(r"def _new\(([^)]*)\)", content)
        if param_match:
            param_str = param_match.group(1)
            params = [x.strip().split(":")[0].split("=")[0].strip() for x in param_str.split(",")]
            params = [x for x in params if x and x not in ("cls", "*", "")]
            call_args = ", ".join(f"{p}={p}" for p in params)
            obj_name = p.parent.name  # aggregate name from dir name
            factory_name = "create" if "def create(" not in orig else "new"
            wrapper = f"""    @classmethod
    def {factory_name}({param_str}) -> {obj_name.title().replace('_', '')}:
        return cls._new({call_args})
"""
            content = re.sub(
                r"    @classmethod\n    def restore\(",
                wrapper + "    @classmethod\n    def restore(",
                content,
            )

    if content != orig:
        p.write_text(content, "utf-8")
        print(f"FIXED: {f['path']}")
    else:
        print(f"SKIP: {f['path']}")

print("\nDone")
