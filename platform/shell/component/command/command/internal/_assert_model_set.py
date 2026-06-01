def _assert_model_set(model: str) -> None:
    if not model:
        raise ValueError("[Command] Required field missing: 'model'")
