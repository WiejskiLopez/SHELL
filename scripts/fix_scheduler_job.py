#!/usr/bin/env python
"""Fix scheduler_job event placement."""

from pathlib import Path

fp = Path("shell/domain/scheduling/aggregates/scheduler_job/scheduler_job.py")
content = fp.read_text("utf-8")

old = (
    "    def _delete(self) -> None:\n"
    '        raise NotImplementedError("_delete() not yet implemented")\n'
    "\n"
    "    def _update(self) -> None:\n"
    '        raise NotImplementedError("_update() not yet implemented")\n'
    "        instance.append_event(\n"
    "            SchedulerJobCreatedEvent.now(\n"
    "                schedulerjob_id=instance.id,\n"
    "                now=now,\n"
    "            )\n"
    "        )\n"
    "        return instance\n"
    "    @property"
)

new = (
    "        instance.append_event(\n"
    "            SchedulerJobCreatedEvent.now(\n"
    "                schedulerjob_id=instance.id,\n"
    "                now=now,\n"
    "            )\n"
    "        )\n"
    "        return instance\n"
    "\n"
    "    def _delete(self) -> None:\n"
    '        raise NotImplementedError("_delete() not yet implemented")\n'
    "\n"
    "    def _update(self) -> None:\n"
    '        raise NotImplementedError("_update() not yet implemented")\n'
    "\n"
    "    @property"
)

if old in content:
    content = content.replace(old, new)
    fp.write_text(content, "utf-8")
    print("FIXED: scheduler_job event moved to _new")
else:
    print("NOT FOUND: pattern didn't match - checking file...")
    import re

    idx = content.find("def _delete")
    if idx >= 0:
        print(content[idx : idx + 400])
