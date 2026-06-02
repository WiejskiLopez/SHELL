from __future__ import annotations

from shell.component.prompt_repo.internal._bootstrap_role_prompts import _bootstrap_role_prompts
from shell.component.prompt_repo.internal._get_current_prompt import _get_current_prompt
from shell.component.prompt_repo.internal._get_prompt_by_id import _get_prompt_by_id
from shell.component.prompt_repo.internal._import_prompt_if_changed import _import_prompt_if_changed
from shell.component.prompt_repo.internal._import_task_prompts import _import_task_prompts
from shell.component.prompt_repo.internal._init_prompt_repo import _init_prompt_repo
from shell.component.prompt_repo.internal._list_prompts_for_task import _list_prompts_for_task
from shell.component.prompt_repo.prompt_record import PromptRecord
from shell.memory.sql_driver.sql_driver import SqlDriver
from shell.utils.path.path import PathType


class PromptRepo:

    __slots__ = ("_driver",)

    def __init__(self) -> None:
        self._driver: SqlDriver | None = None

    @property
    def driver_(self) -> SqlDriver:
        return self._driver

    def init_prompt_repo(self, driver: SqlDriver) -> None:
        _init_prompt_repo(self, driver)

    def import_prompt_if_changed(
        self,
        kind: str,
        name: str,
        body: str,
        role: str | None = None,
        task_id: int | None = None,
        source_uri: str | None = None,
    ) -> PromptRecord:
        return _import_prompt_if_changed(
            self,
            kind=kind,
            name=name,
            body=body,
            role=role,
            task_id=task_id,
            source_uri=source_uri,
        )

    def get_prompt_by_id(self, prompt_id: int) -> PromptRecord | None:
        return _get_prompt_by_id(self, prompt_id)

    def get_current_prompt(
        self,
        kind: str,
        name: str,
        role: str | None = None,
        task_id: int | None = None,
    ) -> PromptRecord | None:
        return _get_current_prompt(self, kind=kind, name=name, role=role, task_id=task_id)

    def list_prompts_for_task(
        self,
        task_id: int,
        kind: str | None = None,
        role: str | None = None,
    ) -> list[PromptRecord]:
        return _list_prompts_for_task(self, task_id=task_id, kind=kind, role=role)

    def bootstrap_role_prompts(self, role_prompts_dir: PathType) -> int:
        return _bootstrap_role_prompts(self, role_prompts_dir)

    def import_task_prompts(self, task_id: int, task_name: str, source_dir: PathType) -> int:
        return _import_task_prompts(self, task_id=task_id, task_name=task_name, source_dir=source_dir)
