from __future__ import annotations

from typing import TYPE_CHECKING

from shell.component.prompt_repo.internal._apply_prompt_schema import _apply_prompt_schema

if TYPE_CHECKING:
    from shell.component.prompt_repo.prompt_repo import PromptRepo
    from shell.memory.sql_driver.sql_driver import SqlDriver


def _init_prompt_repo(repo: 'PromptRepo', driver: 'SqlDriver') -> None:
    repo._driver = driver
    _apply_prompt_schema(driver)
