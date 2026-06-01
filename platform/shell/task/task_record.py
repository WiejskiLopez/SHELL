"""task_record.py
TaskRecord — immutable value object representing one row of the `task` table.
"""

from __future__ import annotations


class TaskRecord:

    __slots__ = (
        "_task_id",
        "_name",
        "_version",
        "_content_hash",
        "_body_md",
        "_body_yaml_raw",
        "_source_md_uri",
        "_source_yaml_uri",
        "_is_current",
        "_created_at",
    )

    def __init__(
        self,
        task_id: int,
        name: str,
        version: int,
        content_hash: str,
        body_md: str,
        body_yaml_raw: str,
        source_md_uri: str | None,
        source_yaml_uri: str | None,
        is_current: bool,
        created_at: str,
    ) -> None:
        self._task_id = task_id
        self._name = name
        self._version = version
        self._content_hash = content_hash
        self._body_md = body_md
        self._body_yaml_raw = body_yaml_raw
        self._source_md_uri = source_md_uri
        self._source_yaml_uri = source_yaml_uri
        self._is_current = is_current
        self._created_at = created_at

    @property
    def task_id_(self) -> int:
        return self._task_id

    @property
    def name_(self) -> str:
        return self._name

    @property
    def version_(self) -> int:
        return self._version

    @property
    def content_hash_(self) -> str:
        return self._content_hash

    @property
    def body_md_(self) -> str:
        return self._body_md

    @property
    def body_yaml_raw_(self) -> str:
        return self._body_yaml_raw

    @property
    def source_md_uri_(self) -> str | None:
        return self._source_md_uri

    @property
    def source_yaml_uri_(self) -> str | None:
        return self._source_yaml_uri

    @property
    def is_current_(self) -> bool:
        return self._is_current

    @property
    def created_at_(self) -> str:
        return self._created_at
