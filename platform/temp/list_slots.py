"""list_slots.py
Skanuje pliki .py w podanym katalogu, zbiera wszystkie klasy z __slots__
i generuje posortowany plik class_slots.md (class_name, slot_name).

Użycie:
    python utils/list_slots.py [katalog] [--out PLIK]

Domyślnie skanuje platform/shell i zapisuje do utils/class_slots.md.

Przykłady:
    python utils/list_slots.py
    python utils/list_slots.py platform/shell --out utils/class_slots.md
"""

from __future__ import annotations

from shell.utils.path.path import Path, PathType
import ast
import argparse
import sys


def collect_slots(root: PathType) -> list[tuple[str, str]]:
    rows = []
    for path in sorted(root.rglob("*.py")):
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                if not isinstance(item, ast.Assign):
                    continue
                for target in item.targets:
                    if not (isinstance(target, ast.Name) and target.id == "__slots__"):
                        continue
                    slots = _extract_slots(item.value)
                    for slot in slots:
                        rows.append((node.name, slot))
    return sorted(rows, key=lambda r: (r[0].lower(), r[1].lower()))


def _extract_slots(node: ast.expr) -> list[str]:
    if isinstance(node, (ast.Tuple, ast.List)):
        return [elt.value for elt in node.elts if isinstance(elt, ast.Constant) and isinstance(elt.value, str)]
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    return []


def write_md(rows: list[tuple[str, str]], out: PathType) -> None:
    lines = ["# class_slots\n", "\n", "| class_name | slot_name |\n", "|---|---|\n"]
    for class_name, slot_name in rows:
        lines.append(f"| {class_name} | {slot_name} |\n")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(lines), encoding="utf-8")
    print(f"Zapisano {len(rows)} wierszy do {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generuje class_slots.md ze __slots__ w kodzie Python.")
    parser.add_argument("directory", nargs="?", default="platform/shell", help="Katalog do skanowania")
    parser.add_argument("--out", default="utils/class_slots.md", help="Plik wyjściowy")
    args = parser.parse_args()

    project_root = Path.new(__file__).parent.parent
    scan_dir = project_root / args.directory
    out_file = project_root / args.out

    if not scan_dir.exists():
        print(f"Błąd: katalog '{scan_dir}' nie istnieje.", file=sys.stderr)
        sys.exit(1)

    rows = collect_slots(scan_dir)
    write_md(rows, out_file)


if __name__ == "__main__":
    main()
