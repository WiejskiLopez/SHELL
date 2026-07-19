#!/usr/bin/env python3
"""Refactor UpdatedAt/DeletedAt to Option Pattern (VO never None, .value can be None)."""

import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "shell"


def main():
    # Step 1: Fix UpdatedAt VO definition
    print("=== Step 1: Fixing UpdatedAt VO definition ===")
    fpath = BASE / "platform/domain/value_objects/updated_at.py"
    content = fpath.read_text(encoding="utf-8")

    # Change value type to optional
    content = content.replace("value: datetime", "value: datetime | None")
    # Add None guard in __post_init__
    content = content.replace(
        "if self.value.tzinfo is None:",
        "if self.value is not None and self.value.tzinfo is None:"
    )
    # Make __str__ handle None
    content = content.replace(
        "return self.value.isoformat()",
        'return self.value.isoformat() if self.value is not None else ""'
    )
    # Make from_datetime accept None
    content = content.replace(
        "def from_datetime(cls, dt: datetime) -> UpdatedAt:",
        "def from_datetime(cls, dt: datetime | None) -> UpdatedAt:"
    )
    content = content.replace(
        "if dt is not None and dt.tzinfo is None:",
        ""
    )
    content = content.replace(
        "def from_datetime(cls, dt: datetime | None) -> UpdatedAt:\n        if dt.tzinfo is None:",
        "def from_datetime(cls, dt: datetime | None) -> UpdatedAt:\n        if dt is not None and dt.tzinfo is None:"
    )
    # Make to_timestamp return None
    content = content.replace(
        "def to_timestamp(self) -> Timestamp:",
        "def to_timestamp(self) -> Timestamp | None:"
    )
    content = content.replace(
        "return Timestamp(self.value)",
        "return Timestamp(self.value) if self.value is not None else None"
    )
    fpath.write_text(content, encoding="utf-8")
    print(f"  Updated: {fpath.relative_to(BASE.parent)}")

    # Step 2: Bulk-replace type annotations in ALL .py files
    print("\n=== Step 2: Bulk-replacing `None` in type annotations ===")
    py_files = sorted(BASE.rglob("*.py"))

    for fpath in py_files:
        original = fpath.read_text(encoding="utf-8")
        content = original

        # Replace 'UpdatedAt | None' with 'UpdatedAt' 
        content = content.replace("UpdatedAt | None", "UpdatedAt")
        # Replace 'DeletedAt | None' with 'DeletedAt'
        content = content.replace("DeletedAt | None", "DeletedAt")

        if content != original:
            fpath.write_text(content, encoding="utf-8")
            print(f"  Types: {fpath.relative_to(BASE.parent)}")

    # Step 3: Fix domain aggregate field/param defaults
    print("\n=== Step 3: Fixing field defaults ===")
    for fpath in py_files:
        original = fpath.read_text(encoding="utf-8")
        content = original

        # Field annotations: _updated_at: UpdatedAt = None → _updated_at: UpdatedAt = UpdatedAt(value=None)
        content = content.replace("_updated_at: UpdatedAt = None", "_updated_at: UpdatedAt = UpdatedAt(value=None)")
        content = content.replace("_deleted_at: DeletedAt = None", "_deleted_at: DeletedAt = DeletedAt(value=None)")

        # Field assignments: self._updated_at = None → self._updated_at = UpdatedAt(value=None)
        content = content.replace("self._updated_at = None", "self._updated_at = UpdatedAt(value=None)")
        content = content.replace("self._deleted_at = None", "self._deleted_at = DeletedAt(value=None)")

        # Constructor param defaults: updated_at: UpdatedAt = None → updated_at: UpdatedAt = UpdatedAt(value=None)
        content = content.replace("updated_at: UpdatedAt = None", "updated_at: UpdatedAt = UpdatedAt(value=None)")
        content = content.replace("deleted_at: DeletedAt = None", "deleted_at: DeletedAt = DeletedAt(value=None)")

        # Also catch: : UpdatedAt = None at function-start lines (already handled above with updated_at:)
        # But also for restore() params and similar
        # _restore_updated_at: UpdatedAt = None → _restore_updated_at: UpdatedAt = UpdatedAt(value=None)?
        # Probably not — let's not guess

        if content != original:
            fpath.write_text(content, encoding="utf-8")
            print(f"  Defaults: {fpath.relative_to(BASE.parent)}")

    # Step 4: Fix mapper patterns (entity_to_model and update_model)
    print("\n=== Step 4: Fixing entity_to_model/update_model patterns ===")

    # Multi-line pattern: entity.updated_at.value\n        if entity.updated_at\n        else None
    # This is tricky. Let me use regex.
    # Pattern: e\|model\|...\.updated_at\.value\s*[\n\s]+if \w+\.updated_at\s*[\n\s]+else None
    # Similarly for deleted_at.

    for fpath in py_files:
        original = fpath.read_text(encoding="utf-8")
        content = original

        # === Single-line .value patterns ===
        # entity.updated_at.value if entity.updated_at else None → entity.updated_at.value
        content = re.sub(
            r'(\w+)\.updated_at\.value\s+if\s+\1\.updated_at\s+else\s+None',
            r'\1.updated_at.value',
            content
        )
        # entity.deleted_at.value if entity.deleted_at else None → entity.deleted_at.value
        content = re.sub(
            r'(\w+)\.deleted_at\.value\s+if\s+\1\.deleted_at\s+else\s+None',
            r'\1.deleted_at.value',
            content
        )
        # entity.updated_at.value if entity.updated_at is not None else None → entity.updated_at.value
        content = re.sub(
            r'(\w+)\.updated_at\.value\s+if\s+\1\.updated_at\s+is not None\s+else\s+None',
            r'\1.updated_at.value',
            content
        )
        # entity.deleted_at.value if entity.deleted_at is not None else None → entity.deleted_at.value
        content = re.sub(
            r'(\w+)\.deleted_at\.value\s+if\s+\1\.deleted_at\s+is not None\s+else\s+None',
            r'\1.deleted_at.value',
            content
        )

        # === Multi-line .value patterns (continuation lines with indentation) ===
        # entity.updated_at.value\n            if entity.updated_at\n            else None
        content = re.sub(
            r'(\w+)\.updated_at\.value\s*\n\s*if\s+\1\.updated_at\s*\n\s*else\s+None',
            r'\1.updated_at.value',
            content
        )
        content = re.sub(
            r'(\w+)\.deleted_at\.value\s*\n\s*if\s+\1\.deleted_at\s*\n\s*else\s+None',
            r'\1.deleted_at.value',
            content
        )
        # Multi-line with `is not None`
        content = re.sub(
            r'(\w+)\.updated_at\.value\s*\n\s*if\s+\1\.updated_at\s+is not None\s*\n\s*else\s+None',
            r'\1.updated_at.value',
            content
        )
        content = re.sub(
            r'(\w+)\.deleted_at\.value\s*\n\s*if\s+\1\.deleted_at\s+is not None\s*\n\s*else\s+None',
            r'\1.deleted_at.value',
            content
        )

        # === Single-line from_datetime patterns ===
        # UpdatedAt.from_datetime(model.updated_at) if model.updated_at else None
        content = re.sub(
            r'UpdatedAt\.from_datetime\(([^)]+)\)\s+if\s+(\w+)\.updated_at\s+else\s+None',
            r'UpdatedAt.from_datetime(\1)',
            content
        )
        content = re.sub(
            r'DeletedAt\.from_datetime\(([^)]+)\)\s+if\s+(\w+)\.deleted_at\s+else\s+None',
            r'DeletedAt.from_datetime(\1)',
            content
        )
        # UpdatedAt.from_datetime(...) if model.updated_at is not None else None
        content = re.sub(
            r'UpdatedAt\.from_datetime\(([^)]+)\)\s+if\s+(\w+)\.updated_at\s+is not None\s+else\s+None',
            r'UpdatedAt.from_datetime(\1)',
            content
        )
        content = re.sub(
            r'DeletedAt\.from_datetime\(([^)]+)\)\s+if\s+(\w+)\.deleted_at\s+is not None\s+else\s+None',
            r'DeletedAt.from_datetime(\1)',
            content
        )

        # === Multi-line from_datetime patterns ===
        # UpdatedAt.from_datetime(_ensure_utc(model.updated_at))\n        if model.updated_at is not None\n        else None,
        content = re.sub(
            r'UpdatedAt\.from_datetime\(([^)]*)\)\s*\n\s*if\s+(\w+)\.updated_at\s+(is not None)?\s*\n\s*else\s+None',
            r'UpdatedAt.from_datetime(\1)',
            content
        )
        content = re.sub(
            r'DeletedAt\.from_datetime\(([^)]*)\)\s*\n\s*if\s+(\w+)\.deleted_at\s+(is not None)?\s*\n\s*else\s+None',
            r'DeletedAt.from_datetime(\1)',
            content
        )

        # === Controller patterns in framework/ ===
        # user.updated_at.value if user.updated_at else None → user.updated_at.value
        content = re.sub(
            r'(\w+)\.updated_at\.value\s+if\s+\1\.updated_at\s+else\s+None',
            r'\1.updated_at.value',
            content
        )
        content = re.sub(
            r'(\w+)\.deleted_at\.value\s+if\s+\1\.deleted_at\s+else\s+None',
            r'\1.deleted_at.value',
            content
        )

        if content != original:
            fpath.write_text(content, encoding="utf-8")
            print(f"  Mapper: {fpath.relative_to(BASE.parent)}")

    # Step 5: Fix _created_at_value function signature
    print("\n=== Step 5: Fixing _created_at_value helper ===")
    # The helper modifies DeletedAt — need to change type hint since DeletedAt is never None
    # Actually, the type `CreatedAt | DeletedAt | datetime | None` stays the same since
    # datetime|None is still present for other callers.
    # But the `if dt is None` branch can now only be hit for `None` literal or datetime|None
    # which is still correct. No change needed.
    print("  No changes needed — _created_at_value already handles all cases")

    # Also fix the TYPE_CHECKING import in _created_at_value.py
    fpath = BASE / "infrastructure/execution/graph_execution/persistence/sql/mappers/_created_at_value.py"
    # No change needed for the function logic, but the type annotation was already changed by Step 2
    # from `CreatedAt | DeletedAt | datetime | None` (it didn't have that pattern, so no change)

    print("\n=== Done! ===")


if __name__ == "__main__":
    main()
