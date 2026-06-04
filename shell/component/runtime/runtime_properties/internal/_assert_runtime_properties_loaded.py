def _assert_runtime_properties_loaded(name: str | None) -> None:
    if name is None:
        raise ValueError("[RuntimeProperties] not loaded — call init_runtime() first")
