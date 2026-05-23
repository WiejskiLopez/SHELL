"""python_version_validator.py
Responsible for one thing: validating the Python interpreter version.
"""


class System:
    """Validates that the Python interpreter meets the minimum version requirement."""

    _MIN_VERSION = (3, 10)

    def validate(self, version_info=None):
        import sys
        version_info = version_info or sys.version_info

        if version_info < self._MIN_VERSION:
            raise RuntimeError(
                f"Python {self._MIN_VERSION[0]}.{self._MIN_VERSION[1]}+ required, "
                f"got {version_info[0]}.{version_info[1]}"
            )
