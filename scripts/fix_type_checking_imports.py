#!/usr/bin/env python3
"""Move DeletedAt/UpdatedAt from TYPE_CHECKING to runtime imports where used at runtime."""

import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "shell"

def fix_file(relpath: str) -> bool:
    fpath = BASE / relpath
    if not fpath.exists():
        return False
    content = fpath.read_text(encoding="utf-8")
    original = content

    for name, import_module in [("DeletedAt", "deleted_at"), ("UpdatedAt", "updated_at")]:
        # Find the TYPE_CHECKING block 
        tc_match = re.search(r'if TYPE_CHECKING:\n(  .*\n)*', content, re.MULTILINE)
        if not tc_match:
            continue
        tc_block = tc_match.group()
        
        if name not in tc_block:
            continue
        
        # Check if name is used at runtime (before or after TYPE_CHECKING)
        before_tc = content[:tc_match.start()]
        after_tc = content[tc_match.end():]
        
        if not re.search(rf'\b{name}\b', before_tc + after_tc):
            continue
        
        # Remove import from TYPE_CHECKING block
        new_tc = re.sub(
            rf'    from shell\.platform\.domain\.value_objects\.{import_module} import {name}[^\n]*\n?',
            '',
            tc_block
        )
        content = content[:tc_match.start()] + new_tc + content[tc_match.end():]
        
        # Add runtime import after existing runtime imports (before TYPE_CHECKING)
        # Find the end of the last regular import
        import_end = 0
        for m in re.finditer(r'^from shell.*\n', content, re.MULTILINE):
            if m.start() < content.find("if TYPE_CHECKING:"):
                import_end = m.end()
        
        if import_end > 0:
            content = (
                content[:import_end] +
                f"from shell.platform.domain.value_objects.{import_module} import {name}\n" +
                content[import_end:]
            )
        else:
            # No runtime imports found - add at top
            content = (
                f"from shell.platform.domain.value_objects.{import_module} import {name}\n" +
                content
            )

    if content != original:
        fpath.write_text(content, encoding="utf-8")
        return True
    return False

# Check all aggregate files
files = list(BASE.rglob("*.py"))
for fpath in sorted(files):
    if fpath.is_relative_to(BASE / "domain"):
        rel = fpath.relative_to(BASE.parent).as_posix()
        if fix_file(rel):
            print(f"Fixed: {rel}")

print("Done!")
