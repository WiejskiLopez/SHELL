"""prompt_type.py
PromptType — enum representing the type of a prompt file.
"""

from __future__ import annotations

from enum import Enum


class PromptType(Enum):
    SYSTEM = 'system'
    ROLE = 'role'
    CLI = 'cli'
    NONE = 'none'
