"""check_var_names.py
Finds assignments where local variable name differs from the property name being assigned.
Example bad:  target = node_logs.logs_dir_   (should be: logs_dir = node_logs.logs_dir_)
"""
from __future__ import annotations

from shell.utils.path.path import Path, PathType
import re

base = Path.new(__file__).parent.parent / "shell"
prop_assign = re.compile(r'^\s*(\w+)\s*=\s*[\w.]+\.(\w+)_\s*$')

mismatches = []

for py_file in sorted(base.rglob("*.py")):
    try:
        lines = py_file.read_text(encoding="utf-8").splitlines()
    except Exception:
        continue
    for lineno, line in enumerate(lines, 1):
        m = prop_assign.match(line)
        if not m:
            continue
        local_var = m.group(1)
        prop_base = m.group(2)
        if local_var in ("self", "cls", "return"):
            continue
        if local_var != prop_base:
            rel = py_file.relative_to(base)
            mismatches.append((str(rel), lineno, local_var, prop_base, line.strip()))

print(f"Total mismatches: {len(mismatches)}\n")
for rel, lineno, var, prop, line in mismatches:
    print(f"{rel}:{lineno}  |  {var!r} -> should be {prop!r}  |  {line}")
