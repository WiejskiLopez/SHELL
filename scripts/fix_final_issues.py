#!/usr/bin/env python3
"""Fix remaining issues:
1. _deleted_at is not None -> _deleted_at.value is not None 
2. Truly empty TYPE_CHECKING blocks -> add 'pass'
"""

import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "shell"

# Pattern for the FULL TYPE_CHECKING block (from 'if' to next non-indented line)
full_tc_pattern = re.compile(r'if TYPE_CHECKING:\n(?:[ \t]+.*\n)*', re.MULTILINE)

for fpath in sorted(BASE.rglob("*.py")):
    if "__pycache__" in str(fpath) or ".venv" in str(fpath):
        continue
    content = fpath.read_text(encoding="utf-8")
    original = content

    # Fix _deleted_at is not None -> _deleted_at.value is not None
    content = content.replace("self._deleted_at is not None", "self._deleted_at.value is not None")

    # Fix truly empty TYPE_CHECKING blocks
    def fix_empty_tc(m):
        block = m.group()
        lines = block.split("\n")
        # Check if any line (after the first) has real content
        has_content = False
        for line in lines[1:]:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                has_content = True
                break
        if not has_content:
            return "if TYPE_CHECKING:\n    pass\n"
        return block

    content = full_tc_pattern.sub(fix_empty_tc, content)

    if content != original:
        fpath.write_text(content, encoding="utf-8")
        print(f"Fixed: {fpath.relative_to(BASE.parent)}")

print("Done!")
