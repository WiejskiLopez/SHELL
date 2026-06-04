"""module_status.py
ModuleStatus — lifecycle status for node child modules.

Values:
    NEW   — initial; module constructed, not yet initialized
    INIT  — init method has been called successfully
"""

from __future__ import annotations

from enum import Enum


class ModuleStatus(Enum):
    NEW = 'new'
    INIT = 'init'
