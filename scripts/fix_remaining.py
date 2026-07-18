import re, sys
from pathlib import Path

base = Path(__file__).resolve().parent.parent

def fix_file(path):
    content = path.read_text(encoding="utf-8")
    orig = content
    name = ""
    m = re.search(r"class (\w+)\(.*AggregateRoot", content)
    if m:
        name = m.group(1)

    for method in ["_new", "_delete", "_update"]:
        if method in content:
            continue
        if method == "_new":
            # Find position before properties
            lines = content.split("\n")
            insert_at = len(lines) - 1
            for i, line in enumerate(lines):
                if "@property" in line and i > 5:
                    insert_at = i
                    break
            stub = (
                f"\n    @classmethod\n"
                f"    def _new(cls) -> {name}:\n"
                f"        raise NotImplementedError(\"_new() not yet implemented\")\n"
            )
            lines.insert(insert_at, stub)
            content = "\n".join(lines)
        elif method == "_delete":
            content = content.replace(
                "    def delete(self",
                "    def _delete(self,\n"
            )
            if "def _delete" not in content:
                content = content.replace(
                    "    @property",
                    "    def _delete(self) -> None:\n"
                    "        raise NotImplementedError(\"_delete() not yet implemented\")\n\n"
                    "    @property",
                    1
                )
        elif method == "_update":
            if "def _update" not in content:
                content = content.replace(
                    "    @property",
                    "    def _update(self) -> None:\n"
                    "        raise NotImplementedError(\"_update() not yet implemented\")\n\n"
                    "    @property",
                    1
                )

    if content != orig:
        path.write_text(content, encoding="utf-8")
        return True
    return False

fixed = 0
for path in sorted(base.rglob("shell/domain/**/aggregates/**/*.py")):
    if any(p in path.parts for p in ("events","exceptions","value_objects","repositories","__init__")):
        continue
    if "AggregateRoot" not in path.read_text(encoding="utf-8"):
        continue
    if fix_file(path):
        print(f"FIXED: {path.relative_to(base)}")
        fixed += 1

print(f"\nFixed {fixed} files")
