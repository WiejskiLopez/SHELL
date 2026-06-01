"""dialect.py
Dialect — value object describing SQL dialect specifics for a SqlDriver.

Slots:
    _placeholder    — placeholder string used by the driver ('?' for sqlite, '%s' for psycopg)
    _auto_pk        — SQL fragment for auto-incrementing integer primary key
    _blob_type      — column type for binary blobs ('BLOB' or 'BYTEA')
    _supports_fts   — whether dialect supports full-text-search on stored data
"""

from __future__ import annotations


class Dialect:
    """SQL dialect descriptor."""

    __slots__ = ("_placeholder", "_auto_pk", "_blob_type", "_supports_fts")

    def __init__(
        self,
        placeholder: str,
        auto_pk: str,
        blob_type: str,
        supports_fts: bool,
    ) -> None:
        self._placeholder: str = placeholder
        self._auto_pk: str = auto_pk
        self._blob_type: str = blob_type
        self._supports_fts: bool = supports_fts

    @property
    def placeholder_(self) -> str:
        return self._placeholder

    @property
    def auto_pk_(self) -> str:
        return self._auto_pk

    @property
    def blob_type_(self) -> str:
        return self._blob_type

    @property
    def supports_fts_(self) -> bool:
        return self._supports_fts

    def render_sql(self, sql: str) -> str:
        if self._placeholder == "?":
            return sql
        out: list[str] = []
        i = 0
        for ch in sql:
            if ch == "?":
                i += 1
                out.append(self._placeholder.replace("$N", str(i)) if "$N" in self._placeholder else self._placeholder)
            else:
                out.append(ch)
        return "".join(out)
