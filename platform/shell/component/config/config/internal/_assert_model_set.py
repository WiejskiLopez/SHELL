def _assert_model_set(config_dict: dict | None) -> None:
    if not config_dict or 'model' not in config_dict:
        raise ValueError("[Config] 'model' key missing in config.yaml")
