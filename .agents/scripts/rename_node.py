"""Rename node → node across the entire codebase (excluding .venv)."""

import pathlib

EXCLUDE_DIRS = {".venv", "__pycache__", ".git", ".mypy_cache", ".pytest_cache", ".ruff_cache"}
EXCLUDE_FILES = {__file__}  # exclude this script itself
ROOT = pathlib.Path(r"C:\Users\palysiewicz\IdeaProjects\SHELL")

REPLACEMENTS = [
    ("NODE", "NODE"),
    ("node", "node"),
    ("Node", "Node"),
]


def should_exclude(path: pathlib.Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    return False


def process_file(filepath: pathlib.Path) -> bool:
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False

    new_content = content
    for old, new in REPLACEMENTS:
        new_content = new_content.replace(old, new)

    if new_content != content:
        filepath.write_text(new_content, encoding="utf-8")
        return True
    return False


def main():
    changed = 0
    total = 0
    for filepath in ROOT.rglob("*"):
        if filepath.is_file() and not filepath.name.startswith("."):
            if should_exclude(filepath):
                continue
            total += 1
            if process_file(filepath):
                changed += 1
                print(f"  CHANGED: {filepath.relative_to(ROOT)}")

    print(f"\nProcessed {total} files, changed {changed} files.")


if __name__ == "__main__":
    main()
