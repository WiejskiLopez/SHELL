#!/usr/bin/env python3
"""Move DeletedAt from TYPE_CHECKING to runtime imports in all files that use it at runtime."""

import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "shell"

# Find all files with DeletedAt or UpdatedAt in TYPE_CHECKING used at runtime
for fpath in sorted(BASE.rglob("*.py")):
    if "__pycache__" in str(fpath) or ".venv" in str(fpath):
        continue
    content = fpath.read_text(encoding="utf-8")
    original = content

    for name, mod in [("DeletedAt", "deleted_at"), ("UpdatedAt", "updated_at")]:
        # Check if name is in TYPE_CHECKING block
        tc_match = re.search(r'if TYPE_CHECKING:\n(  .*\n)*', content)
        if not tc_match:
            continue
        tc_block = tc_match.group()
        if name not in tc_block:
            continue

        # Check runtime usage
        runtime = content[:tc_match.start()] + content[tc_match.end():]
        if not re.search(rf'\b{name}\b', runtime):
            continue

        # Remove the import from TYPE_CHECKING
        escaped_mod = re.escape(mod)
        escaped_name = re.escape(name)
        # Pattern: `    from shell.platform.domain.value_objects.deleted_at import DeletedAt\n`
        pattern = rf'    from shell\.platform\.domain\.value_objects\.{escaped_mod} import {escaped_name}\n?'
        new_tc = re.sub(pattern, '', tc_block)

        if new_tc == tc_block:
            # The pattern didn't match; try multi-line format
            pattern = rf'    from shell\.platform\.domain\.value_objects\.{escaped_mod} import \({escaped_name}\)\n?'
            new_tc = re.sub(pattern, '', tc_block)

        content = content[:tc_match.start()] + new_tc + content[tc_match.end():]

        # Add runtime import after the last existing from-shell import outside TYPE_CHECKING
        # Find the last import line before TYPE_CHECKING
        lines = content.splitlines(keepends=True)
        insert_pos = 0
        in_type_checking = False
        last_runtime_import_end = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("if TYPE_CHECKING:"):
                in_type_checking = True
            if line.strip().startswith("from ") and not in_type_checking:
                last_runtime_import_end = i + 1  # after this line
            if in_type_checking and not line.startswith(" "):
                in_type_checking = False

        import_line = f"from shell.platform.domain.value_objects.{mod} import {name}\n"
        lines.insert(last_runtime_import_end, import_line)
        # Adjust: insert_pos is the index where imports end
        # Actually, let me redo this more carefully

    if content != original:
        fpath.write_text(content, encoding="utf-8")
        print(f"Fixed: {fpath.relative_to(BASE.parent)}")

print("Done!")
