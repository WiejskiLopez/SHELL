#!/usr/bin/env python
import re
content = open("shell/domain/scheduling/aggregates/scheduler_execution/scheduler_execution.py").read()
orig = content

content = re.sub(
    r'    @classmethod\n    def _new\(cls\) -> \w+:\n        raise NotImplementedError\("_new\(\) not yet implemented"\)\n?',
    "",
    content,
)

content = content.replace("    def create(", "    def _new(", 1)

sig_match = re.search(r"def _new\(([^)]+)\)", content)
if sig_match:
    sig = sig_match.group(1)
    params = [x.strip().split(":")[0].split("=")[0].strip() for x in sig.split(",")]
    params = [p for p in params if p and p not in ("cls", "*", "")]
    call_args = ", ".join(f"{p}={p}" for p in params)
    wrapper = f'''    @classmethod
    def create({sig}) -> SchedulerExecution:
        return cls._new({call_args})

'''
    content = content.replace(
        "    @classmethod\n    def restore(",
        wrapper + "    @classmethod\n    def restore(",
    )

if content != orig:
    open("shell/domain/scheduling/aggregates/scheduler_execution/scheduler_execution.py", "w").write(content)
    print("FIXED")
