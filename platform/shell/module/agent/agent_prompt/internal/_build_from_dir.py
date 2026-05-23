from __future__ import annotations


from shell.utils.io.io import default_read_utf8_safe
from shell.module.agent.agent_prompt.internal._clean_name import _clean_name
from shell.utils.path.path import Path, PathType

_TEXT_SUFFIXES = {".md", ".txt", ".yaml", ".yml", ".json"}


def _build_from_dir(directory: PathType, reader=None) -> str:
    if reader is None:
        reader = default_read_utf8_safe
    files = sorted(
        (f for f in Path.iterdir(directory) if Path.is_file(f) and f.suffix in _TEXT_SUFFIXES),
        key=lambda f: f.name,
    )

    if not files:
        return ""

    sections: list[str] = []

    for idx, file in enumerate(files, 1):
        sections.append(f"# {idx}. {_clean_name(file.stem)}")
        try:
            sections.append(reader(file))
        except OSError:
            sections.append("<unreadable>")

    return "\n\n".join(sections)
