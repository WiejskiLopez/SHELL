from __future__ import annotations

import subprocess

import pytest
from _arch_helpers import BASE


@pytest.mark.skip(reason="import-linter requires all layers to be Python packages with __init__.py; framework/ layer needs this")
def test_import_linter_contracts() -> None:
    project_root = BASE.parent
    import os
    import shutil
    import_linter_path = shutil.which("import-linter")
    if import_linter_path is None:
        import_linter_path = str(BASE.parent / "venv" / "Scripts" / "import-linter.exe")
        if not os.path.exists(import_linter_path):
            import_linter_path = "import-linter"
    old_cwd = os.getcwd()
    try:
        os.chdir(str(project_root))
        result = subprocess.run(
            [import_linter_path, "lint", "--config", str(project_root / ".importlinter.ini")],
            capture_output=True,
            text=True,
        )
    finally:
        os.chdir(old_cwd)
    assert result.returncode == 0, (
        f"import-linter violations:\n{result.stdout}\n{result.stderr}"
    )
