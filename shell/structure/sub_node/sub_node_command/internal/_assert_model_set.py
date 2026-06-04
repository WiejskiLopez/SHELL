def _assert_model_set(model) -> None:
    if not model:
        raise RuntimeError("[SubNodeCommand] model is not set — pass --model to the CLI")
