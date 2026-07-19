"""Rename files and directories: graph_node → node in their names."""

import os
import pathlib

EXCLUDE_DIRS = {".venv", "__pycache__", ".git", ".mypy_cache", ".pytest_cache", ".ruff_cache"}
ROOT = pathlib.Path(r"C:\Users\palysiewicz\IdeaProjects\SHELL")


def should_exclude(path: pathlib.Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    return False


def rename_item(old_path: pathlib.Path) -> pathlib.Path | None:
    """Rename a file or directory by replacing 'graph_node' with 'node' in its name.
    Returns the new path if renamed, None otherwise."""
    name = old_path.name
    new_name = name.replace("graph_node", "node")
    if new_name == name:
        return None

    new_path = old_path.parent / new_name
    print(f"  {old_path.relative_to(ROOT)}")
    print(f"    -> {new_path.relative_to(ROOT)}")
    os.rename(str(old_path), str(new_path))
    return new_path


def main():
    # Phase 1: Rename files (deep level first)
    print("=== Phase 1: Renaming files ===")
    file_count = 0
    # Get all files, sort by depth (deepest first) to handle nested renames
    files = sorted(
        [
            p
            for p in ROOT.rglob("*")
            if p.is_file() and "graph_node" in p.name and not should_exclude(p)
        ],
        key=lambda p: len(p.parts),
        reverse=True,
    )
    for f in files:
        result = rename_item(f)
        if result:
            file_count += 1
    print(f"Renamed {file_count} files.\n")

    # Phase 2: Rename directories (deepest first)
    print("=== Phase 2: Renaming directories ===")
    dir_count = 0
    dirs = sorted(
        [
            p
            for p in ROOT.rglob("*")
            if p.is_dir() and "graph_node" in p.name and not should_exclude(p)
        ],
        key=lambda p: len(p.parts),
        reverse=True,
    )
    for d in dirs:
        result = rename_item(d)
        if result:
            dir_count += 1
    print(f"Renamed {dir_count} directories.\n")

    print("Done!")


if __name__ == "__main__":
    main()
