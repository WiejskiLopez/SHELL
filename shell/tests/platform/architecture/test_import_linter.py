from __future__ import annotations

import os
import shutil
import subprocess

from _arch_helpers import BASE


def test_import_linter_contracts() -> None:
    project_root = BASE.parent
    import_linter_path = shutil.which("import-linter")
    if import_linter_path is None:
        import_linter_path = str(BASE.parent / "venv" / "Scripts" / "import-linter.exe")
        if not os.path.exists(import_linter_path):
            import_linter_path = "import-linter"
    old_cwd = os.getcwd()
    try:
        os.chdir(str(project_root))
        result = subprocess.run(
            [import_linter_path, "lint"],
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(old_cwd)
    assert result.returncode == 0, f"import-linter violations:\n{result.stdout}\n{result.stderr}"
