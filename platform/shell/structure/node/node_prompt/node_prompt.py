"""node_prompt.py
NodePrompt: loads all *.prompt.md files from task_dir into a list.

Slots:
    _app           — parent App
    _prompt_dir    — resolved path to the prompt directory
    _prompt        — Prompt instance; file_prompts_ holds loaded *.prompt.md files
    _module_status — ModuleStatus enum; NEW on construction, INIT after init_node_prompt()

Methods:
    init_node_prompt() — load all *.prompt.md files from task_dir into file_prompt_list
"""

from __future__ import annotations

from shell.utils.path.path import PathType


from shell.status.module_status.module_status import ModuleStatus
from shell.structure.node.node_prompt.internal._init_node_prompt import _init_node_prompt
from shell.component.prompt.prompt.prompt import Prompt


class NodePrompt:

    __slots__ = ("_app", "_prompt_dir", "_prompt", "_module_status")

    def __init__(self, app) -> None:
        self._app = app
        self._prompt_dir: PathType | None = None
        self._prompt: Prompt | None = None
        self._module_status: ModuleStatus = ModuleStatus.NEW

    @property
    def prompt_dir_(self) -> PathType:
        return self._prompt_dir

    @property
    def prompt_(self) -> Prompt:
        if self._prompt is None:
            self._prompt = Prompt(self._app)
        return self._prompt

    @property
    def module_status_(self) -> ModuleStatus:
        return self._module_status

    def init_node_prompt(self) -> None:
        _init_node_prompt(self)
        self._module_status = ModuleStatus.INIT
