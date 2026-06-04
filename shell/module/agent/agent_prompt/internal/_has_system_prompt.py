"""_has_system_prompt.py
Private. Responsible for one thing: checking whether a system prompt file
for the given role already exists in the input/ directory.
"""

import re

from shell.utils.path.path import Path, PathType


def _has_system_prompt(input_dir: PathType, role: str) -> bool:
    if not Path.is_dir(input_dir):
        return False
    pattern = re.compile(rf'^\d{{4}}_system_{re.escape(role)}\.md$')
    return any(pattern.match(f.name) for f in Path.iterdir(input_dir) if Path.is_file(f))
