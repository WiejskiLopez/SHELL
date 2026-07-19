#!/usr/bin/env python3
"""Remove empty if TYPE_CHECKING: blocks from all shell files."""

import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "shell"

for fpath in sorted(BASE.rglob("*.py")):
    if "__pycache__" in str(fpath) or ".venv" in str(fpath):
        continue
    content = fpath.read_text(encoding="utf-8")
    original = content

    # Remove empty TYPE_CHECKING blocks (only blank/comment lines)
    content = re.sub(
        r'if TYPE_CHECKING:\n(?:[ \t]*#[^\n]*\n|[ \t]*\n)*',
        '',
        content
    )

    if content != original:
        fpath.write_text(content, encoding="utf-8")
        print(f"Fixed: {fpath.relative_to(BASE.parent)}")

print("Done!")
