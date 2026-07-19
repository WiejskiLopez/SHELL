#!/usr/bin/env python
"""Fix create() and restore() parameter order in all aggregates."""

from __future__ import annotations

import re
from pathlib import Path


def extract_method(
    content: str, method_name: str
) -> tuple[int, int, str, list[str], list[str]] | None:
    """Extract a method's full text, params, and body."""
    pattern = f"    @classmethod\n    def {method_name}("
    idx = content.find(pattern)
    if idx < 0:
        return None

    # First find the signature end to know where the method body starts
    # Find the closing paren of the full method signature
    full_text = content[idx:]
    paren_start = full_text.find("(")
    if paren_start < 0:
        return None
    depth = 1
    sig_paren_end = paren_start + 1
    while depth > 0 and sig_paren_end < len(full_text):
        if full_text[sig_paren_end] == "(":
            depth += 1
        elif full_text[sig_paren_end] == ")":
            depth -= 1
            if depth == 0:
                sig_paren_end += 1
                break
        sig_paren_end += 1
    if depth != 0:
        return None

    # Find the : after the closing paren
    colon = full_text.find(":\n", sig_paren_end)
    if colon < 0:
        return None

    # Now find the next method in the body
    body_start = idx + colon + 2
    next_method = re.search(
        r"\n    (?:(?:@(?:classmethod|property|staticmethod)\n))", content[body_start:]
    )
    if next_method:
        end = body_start + next_method.start()
    else:
        end = len(content)

    full_text = content[idx:end]
    sig_text = content[idx : idx + colon + 1]
    body_text = content[body_start:end]

    # Extract params from signature
    paren = sig_text.find("(")
    if paren < 0:
        return None

    params_str = sig_text[paren + 1 : sig_text.rfind(")")]

    # Parse individual params
    params = []
    current = ""
    depth = 0
    for ch in params_str:
        if ch in "({[":
            depth += 1
            current += ch
        elif ch in ")}]":
            depth -= 1
            current += ch
        elif ch == "," and depth == 0:
            params.append(current.strip())
            current = ""
        else:
            current += ch
    if current.strip():
        params.append(current.strip())

    # Also get the return type
    return_arrow = sig_text.find(") ->")
    return_type = ""
    if return_arrow >= 0:
        return_type = sig_text[return_arrow + 4 :].strip()

    return (idx, end, return_type, params, body_text.split("\n"))


def reorder_create_params(params: list[str]) -> list[str]:
    """Reorder: cls/self, *, id_/id, now, business, optional."""
    result = []
    fixed_start = []

    for p in params:
        if p in ("self", "cls", "*", "*,", "*,\n"):
            fixed_start.append(p)
        else:
            break

    remaining = params[len(fixed_start) :]

    id_param = None
    now_param = None
    business = []
    optional = []

    for p in remaining:
        name = p.split(":")[0].split("=")[0].strip().rstrip(",")
        if name in ("id_", "id"):
            id_param = p
        elif name == "now":
            now_param = p
        elif "=" in p:
            optional.append(p)
        else:
            business.append(p)

    if id_param:
        result.append(id_param)
    if now_param:
        result.append(now_param)
    result.extend(business)
    result.extend(optional)

    return result


def reorder_restore_params(params: list[str]) -> list[str]:
    """Reorder: cls, *, id, created_at, updated_at, deleted_at, business, optional."""
    result = []
    fixed_start = []

    for p in params:
        if p in ("self", "cls", "*", "*,", "*,\n"):
            fixed_start.append(p)
        else:
            break

    remaining = params[len(fixed_start) :]

    id_param = None
    ca_param = None
    ua_param = None
    da_param = None
    business = []
    optional = []

    for p in remaining:
        name = p.split(":")[0].split("=")[0].strip().rstrip(",")
        if name in ("id_", "id"):
            id_param = p
        elif name == "created_at":
            ca_param = p
        elif name == "updated_at":
            ua_param = p
        elif name == "deleted_at":
            da_param = p
        elif "=" in p:
            optional.append(p)
        else:
            business.append(p)

    if id_param:
        result.append(id_param)
    if ca_param:
        result.append(ca_param)
    if ua_param:
        result.append(ua_param)
    if da_param:
        result.append(da_param)
    result.extend(business)
    result.extend(optional)

    return result


def build_method(
    method_name: str, return_type: str, params: list[str], body_lines: list[str]
) -> str:
    """Build the method text from components."""
    indent = "    "
    # Get the first param line to determine indentation
    first_param_line = params[0] if params else ""
    indent_level = len(first_param_line) - len(first_param_line.lstrip()) if first_param_line else 8
    inner = " " * indent_level

    method = f"{indent}@classmethod\n{indent}def {method_name}("

    for p in params:
        p_stripped = p.strip().rstrip(",")
        if p_stripped in ("*,", "*,", "*"):
            method += f"\n{inner}{p_stripped}"
        elif p_stripped == "":
            continue
        else:
            method += f"\n{inner}{p_stripped},"

    if return_type:
        method += f"\n{inner[:4]}) -> {return_type}:\n"
    else:
        method += f"\n{inner[:4]}):\n"

    for line in body_lines:
        method += f"{line}\n"

    return method


def fix_file(path: Path) -> bool:
    content = path.read_text("utf-8")
    # Normalize line endings
    content = content.replace("\r\n", "\n")
    orig = content

    name_match = re.search(r"class (\w+)\(.*AggregateRoot", content)
    if not name_match:
        return False

    for method_name in ("create", "new", "open", "initialize"):
        info = extract_method(content, method_name)
        if info is None:
            continue
        idx, end, return_type, params, body = info

        # Fix _new and create differently
        if method_name == "create" or True:  # All factory methods
            new_params = reorder_create_params(params)
        else:
            continue

        if new_params == params:
            continue

        old_method = content[idx:end]
        new_method = build_method(method_name, return_type, new_params, body)
        content = content[:idx] + new_method + content[end:]

    # Fix restore
    info = extract_method(content, "restore")
    if info:
        idx, end, return_type, params, body = info
        new_params = reorder_restore_params(params)

        if new_params != params:
            old_method = content[idx:end]
            new_method = build_method("restore", return_type, new_params, body)
            content = content[:idx] + new_method + content[end:]

    if content != orig:
        path.write_text(content, "utf-8")
        return True
    return False


def main() -> None:
    count = 0
    for path in sorted(Path("shell/domain").rglob("**/aggregates/**/*.py")):
        if any(
            p in path.parts
            for p in ("events", "exceptions", "value_objects", "repositories", "__init__")
        ):
            continue
        if "AggregateRoot" not in path.read_text("utf-8"):
            continue
        if fix_file(path):
            print(f"FIXED: {path}")
            count += 1
    print(f"\nFixed {count} files")


if __name__ == "__main__":
    main()
