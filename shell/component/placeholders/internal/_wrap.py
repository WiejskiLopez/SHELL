def _wrap(placeholders, text: str) -> str:
    result = text
    for placeholder, value in placeholders._placeholder_list:
        result = result.replace(value, placeholder)
    return result
