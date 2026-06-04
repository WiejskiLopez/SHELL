"""_build_prompt_from_input.py
Private. Responsible for one thing: building the full prompt string from
*.md files already loaded into app.app_node_.node_.node_input_.input_files_map_.
"""

from __future__ import annotations

from shell.utils.path.path import Path, PathType

from shell.module.agent.agent_prompt.internal._clean_name import _clean_name


def _build_prompt_from_input(app, reader=None) -> str:
    input_files_map = app.app_node_.node_.node_input_.input_files_map_
    if not input_files_map:
        return ""

    sections: list[str] = []
    for idx, (file, file_name) in enumerate(input_files_map.items(), 1):
        sections.append(f"# {idx}. {_clean_name(Path.new(file_name).stem)}")
        file_body = file.file_body_
        sections.append(file_body if file_body else "<unreadable>")

    return "\n\n".join(sections)
