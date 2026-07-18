#!/usr/bin/env python
import ast
from pathlib import Path

for f in sorted(Path("shell").rglob("**/*.py")):
    try:
        ast.parse(f.read_text("utf-8"))
    except SyntaxError as e:
        print(f"{f} - line {e.lineno}: {e.msg}")
        lines = f.read_text("utf-8").split("\n")
        for i in range(max(0, e.lineno-3), min(len(lines), e.lineno+2)):
            print(f"{i+1}: {lines[i]}")
