def _assert_model_resolved(model: str | None) -> None:
    if not model:
        raise ValueError("[AppConfiguration] model is not set — define it in CLI args or in runner_root_dir/config/config.yaml")
