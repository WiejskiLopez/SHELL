def _bind_slots(placeholders, obj) -> None:
    for slot in getattr(obj, '__slots__', []):
        value = getattr(obj, slot, None)
        if isinstance(value, str):
            name = slot.lstrip('_')
            placeholders.add_placeholder(name, value)
