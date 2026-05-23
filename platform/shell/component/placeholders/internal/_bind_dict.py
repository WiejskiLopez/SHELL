from shell.component.placeholders.internal._add_placeholder import _add_placeholder
from shell.component.placeholders.internal._set_placeholder import _set_placeholder


def _bind_dict(placeholders, config_dict: dict) -> None:
    existing_tokens = {token for token, _ in placeholders._placeholder_list}
    for key, value in config_dict.items():
        if isinstance(value, str):
            token = f'$${key}$$'
            if token in existing_tokens:
                _set_placeholder(placeholders, key, value)
            else:
                _add_placeholder(placeholders, key, value)
