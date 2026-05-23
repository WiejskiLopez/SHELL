def _assert_config_path_set(path) -> None:
    if not path:
        raise ValueError("[Config] config_path is not set")
