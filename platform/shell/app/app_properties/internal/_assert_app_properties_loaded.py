def _assert_app_properties_loaded(name: str | None) -> None:
    if name is None:
        raise ValueError("[AppProperties] not loaded — call init_app_properties() first")
