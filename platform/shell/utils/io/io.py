from __future__ import annotations

import logging

from shell.utils.path.path import Path


def default_read_utf8(path) -> str:
    return Path.read_text(path)


def default_read_utf8_safe(path) -> str:
    return Path.read_text_safe(path)


def default_write_utf8(path, text: str) -> None:
    Path.write_text(path, text)


def default_make_dirs(path) -> None:
    Path.mkdir(path)


def default_unlink(path) -> None:
    Path.unlink(path)


def default_file_handler(path) -> logging.FileHandler:
    return logging.FileHandler(path, encoding="utf-8")
