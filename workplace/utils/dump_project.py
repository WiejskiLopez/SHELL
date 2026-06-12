from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent / "shell_ddd"
OUTPUT_DIR = Path(__file__).parent
MAX_LINES = 5000
EXTENSIONS = {".py", ".md", ".yaml", ".yml"}
EXCLUDE_DIRS = {
    ".git", "__pycache__", ".idea", ".vscode", "node_modules",
    ".pytest_cache", "*.egg-info", "shell.egg-info",
}


def collect_files() -> list[Path]:
    files = []
    for ext in EXTENSIONS:
        for path in sorted(ROOT.rglob(f"*{ext}")):
            if any(part in EXCLUDE_DIRS or part.endswith(".egg-info") for part in path.parts):
                continue
            if path.is_relative_to(OUTPUT_DIR):
                continue
            files.append(path)
    return sorted(files)


def file_block(path: Path) -> list[str]:
    rel = path.relative_to(ROOT)
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        content = f"[BŁĄD ODCZYTU: {e}]"
    lines = [
        f"### {rel.as_posix()}",
        "```",
        *content.splitlines(),
        "```",
        "",
    ]
    return lines


def dump() -> None:
    files = collect_files()
    if not files:
        print("Brak plików do eksportu.")
        return

    chunk_index = 1
    current_lines: list[str] = []

    def flush(lines: list[str], index: int) -> None:
        out = OUTPUT_DIR / f"dump_{index:03d}.md"
        out.write_text("\n".join(lines), encoding="utf-8")
        print(f"  -> {out.name} ({len(lines)} linii)")

    for path in files:
        block = file_block(path)
        if current_lines and len(current_lines) + len(block) > MAX_LINES:
            flush(current_lines, chunk_index)
            chunk_index += 1
            current_lines = []
        current_lines.extend(block)

    if current_lines:
        flush(current_lines, chunk_index)

    print(f"\nGotowe: {chunk_index} plik(ów) w {OUTPUT_DIR}")


if __name__ == "__main__":
    dump()
