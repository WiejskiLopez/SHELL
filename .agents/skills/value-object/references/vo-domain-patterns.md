# Value Object — wzorce w warstwie domenowej

> Wyciągnięte z `shell-architecture/references/domain.md`.

- `@dataclass(frozen=True, slots=True)`
- Walidacja w `__post_init__`
- Obowiązkowa metoda `__str__`
- Brak tożsamości — dwa VO z tymi samymi wartościami są wymienne
- Typy ID: każda klasa z kompletem `@dataclass(frozen=True, slots=True)`, `__post_init__` (walidacja non-empty), `__str__`, `@classmethod generate()`
