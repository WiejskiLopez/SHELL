def _set_placeholder(placeholders, name: str, value: str) -> None:
    token = f'$${name}$$'
    for index, (placeholder, _) in enumerate(placeholders._placeholder_list):
        if placeholder == token:
            placeholders._placeholder_list[index] = (token, value)
            return
