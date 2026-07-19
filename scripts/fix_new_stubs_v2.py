#!/usr/bin/env python
"""Fix _new stubs correctly: remove stub, rename real factory to _new, add wrapper."""

import re
from pathlib import Path

FILES = [
    "shell/domain/user/aggregates/user/user.py",
    "shell/domain/execution/aggregates/agent_execution/agent_execution.py",
    "shell/domain/execution/aggregates/edge_execution/edge_execution.py",
    "shell/domain/execution/aggregates/graph_execution/graph_execution.py",
    "shell/domain/execution/aggregates/session_execution/session_execution.py",
    "shell/domain/execution/aggregates/task_execution/task_execution.py",
    "shell/domain/execution/aggregates/user_execution/user_execution.py",
]

for path_str in FILES:
    fp = Path(path_str)
    content = fp.read_text("utf-8")
    orig = content

    # 1. Remove NotImplementedError _new stub
    content = re.sub(
        r"    @classmethod\n    def _new\(cls\) -> \w+:\n        raise NotImplementedError\(\"_new\(\) not yet implemented\"\)\n?",
        "",
        content,
    )

    # 2. Find the real factory (new or create) and rename to _new
    for factory in ["new", "create"]:
        if (
            re.search(rf"    @classmethod\n    def {factory}\(", content)
            and f"def _new(" not in content
        ):
            content = re.sub(
                rf"(    @classmethod\n    def ){factory}\(",
                r"\1_new(",
                content,
            )
            break

    # 3. Add public factory wrapper if the public method doesn't exist
    has_public = any(f"    def {fn}(" in content for fn in ["new", "create"])
    if not has_public:
        # Find _new signature
        sig_match = re.search(r"def _new\(([^)]+)\)", content)
        if sig_match:
            sig = sig_match.group(1)
            # Get just param names
            param_names = []
            for p in [x.strip() for x in sig.split(",")]:
                name = p.split(":")[0].split("=")[0].strip()
                if name and name not in ("cls", "*", ""):
                    param_names.append(name)
            call_args = ", ".join(f"{n}={n}" for n in param_names)
            # Get aggregate name
            name_match = re.search(r"class (\w+)\(AggregateRoot", content)
            agg_name = name_match.group(1) if name_match else "Foo"

            wrapper = f"\n    @classmethod\n    def create({sig}) -> {agg_name}:\n        return cls._new({call_args})\n"
            content = content.replace(
                "    @classmethod\n    def restore(",
                wrapper + "\n    @classmethod\n    def restore(",
            )

    if content != orig:
        fp.write_text(content, "utf-8")
        print(f"FIXED: {path_str}")

print("\nDone")
