from __future__ import annotations


from shell.utils.io.io import default_read_utf8_safe
from shell.module.agent.agent_prompt.internal._build_from_dir import _build_from_dir
from shell.module.agent.agent_prompt.internal._find_file import _find_file
from shell.utils.path.path import Path, PathType


def _resolve_prompt(value: str, node: PathType, reader=None) -> str:
    if reader is None:
        reader = default_read_utf8_safe
    path = Path.new(value)

    if Path.is_file(path):
        return reader(path)

    if Path.is_dir(path):
        return _build_from_dir(path, reader=reader)

    if len(path.parts) == 1:
        found_file = _find_file(value, node)
        if found_file:
            return reader(found_file)

    return value
