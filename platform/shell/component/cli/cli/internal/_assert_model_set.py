def _assert_model_set(model: str | None, mode: str | None) -> None:
    if mode == 'agent' and not model:
        raise ValueError("[Cli] --model is required in agent mode")
