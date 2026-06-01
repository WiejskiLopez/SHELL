from __future__ import annotations


from shell.utils.path.path import Path, PathType


def _save_prompt_file(prompt_file, save_dir: PathType) -> None:
    dest = Path.new(save_dir)
    Path.mkdir(dest)
    Path.write_text(dest / prompt_file._file_name, prompt_file._file_body)
