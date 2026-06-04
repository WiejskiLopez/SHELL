from __future__ import annotations

import yaml


def _init_config(config: 'Config', package_name: str, kind: str, source: str, seed_yaml_path=None) -> None:
    try:
        repo = config._app.runner_config_repo_
        if seed_yaml_path is not None:
            raw_text = repo.bootstrap_runner_config(package_name, kind, seed_yaml_path)
        else:
            raw_text = repo.get_runner_config_body(package_name, kind)
        raw = yaml.safe_load(raw_text) or {}
        config._config_dict = {k: {'value': v, 'source': source} for k, v in raw.items()}
    except Exception as exc:
        config._app.app_trace_.record_error_and_raise('config.Config.init_config', exc)
