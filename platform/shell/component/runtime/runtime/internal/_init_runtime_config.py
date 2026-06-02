from __future__ import annotations

from typing import TYPE_CHECKING

from shell.constants.constants import CONFIG_DIR, CONFIG_YAML

if TYPE_CHECKING:
    from shell.component.runtime.runtime.runtime import Runtime


def _init_runtime_config(runtime: Runtime) -> None:
    runner_root = runtime.app_.cli_.cli_properties_.runner_root_dir_
    seed_path = runner_root / CONFIG_DIR / CONFIG_YAML
    runtime.runtime_config_.init_config(
        package_name=runner_root.name,
        kind='config',
        source='runtime',
        seed_yaml_path=seed_path,
    )
