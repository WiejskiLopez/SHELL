def _apply(placeholders, text: str) -> str:
    result = text
    for placeholder, value in placeholders._placeholder_list:
        result = result.replace(placeholder, value)
    return result
