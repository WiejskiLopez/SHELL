def _assert_config_body_loaded(body: str) -> None:
    if not body.strip():
        raise ValueError("[Config] config_file_body is empty — call init_config() first")
