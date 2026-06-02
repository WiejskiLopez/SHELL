from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptRecord:
    prompt_id: int
    kind: str
    task_id: int | None
    role: str | None
    name: str
    body: str
    content_hash: str
    source_uri: str | None
    version: int
    is_current: int
    created_at: str

    @property
    def prompt_id_(self) -> int:
        return self.prompt_id

    @property
    def kind_(self) -> str:
        return self.kind

    @property
    def task_id_(self) -> int | None:
        return self.task_id

    @property
    def role_(self) -> str | None:
        return self.role

    @property
    def name_(self) -> str:
        return self.name

    @property
    def body_(self) -> str:
        return self.body

    @property
    def content_hash_(self) -> str:
        return self.content_hash

    @property
    def version_(self) -> int:
        return self.version
