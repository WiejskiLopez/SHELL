"""path.py
Path — static proxy for file and directory operations on a pathlib.Path.
"""

from __future__ import annotations

import shutil
from pathlib import Path as _Path


PathType = _Path


class Path:
    """Static proxy for file and directory operations on a pathlib.Path."""

    @staticmethod
    def new(*args) -> _Path:
        return _Path(*args)

    @staticmethod
    def mkdir(path: PathType) -> None:
        path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def exists(path: PathType) -> bool:
        return path.exists()

    @staticmethod
    def is_file(path: PathType) -> bool:
        return path.is_file()

    @staticmethod
    def is_dir(path: PathType) -> bool:
        return path.is_dir()

    @staticmethod
    def read_text(path: PathType) -> str:
        return path.read_text(encoding='utf-8')

    @staticmethod
    def write_text(path: PathType, text: str) -> None:
        path.write_text(text, encoding='utf-8')

    @staticmethod
    def unlink(path: PathType) -> None:
        path.unlink()

    @staticmethod
    def rmtree(path: PathType) -> None:
        shutil.rmtree(path)

    @staticmethod
    def copy_to(src: PathType, dest: PathType) -> None:
        shutil.copy2(src, dest)

    @staticmethod
    def move(src: PathType, dest: PathType) -> None:
        shutil.move(str(src), str(dest))

    @staticmethod
    def is_symlink(path: PathType) -> bool:
        return path.is_symlink()

    @staticmethod
    def iterdir(path: PathType) -> list[PathType]:
        return list(path.iterdir())

    @staticmethod
    def glob(path: PathType, pattern: str) -> list[PathType]:
        return sorted(path.glob(pattern))

    @staticmethod
    def rglob(path: PathType, pattern: str) -> list[PathType]:
        return sorted(path.rglob(pattern))

    @staticmethod
    def read_text_safe(path: PathType) -> str:
        return path.read_text(encoding='utf-8', errors='replace')
