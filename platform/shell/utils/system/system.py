"""python_version_validator.py
Responsible for one thing: validating the Python interpreter version.
"""

from __future__ import annotations

import os
import shutil
import sys


class System:
    """Validates that the Python interpreter meets the minimum version requirement."""

    _MIN_VERSION = (3, 10)

    def validate(self, version_info=None):
        version_info = version_info or sys.version_info

        if version_info < self._MIN_VERSION:
            raise RuntimeError(
                f"Python {self._MIN_VERSION[0]}.{self._MIN_VERSION[1]}+ required, "
                f"got {version_info[0]}.{version_info[1]}"
            )

    @staticmethod
    def env() -> dict:
        return os.environ

    @staticmethod
    def os_name() -> str:
        return os.name

    @staticmethod
    def which(name: str) -> str | None:
        return shutil.which(name)
