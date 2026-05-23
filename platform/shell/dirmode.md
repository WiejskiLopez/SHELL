# Architektura DOM

Struktura oparta na drzewie obiektów, którego korzeniem jest klasa `App`.
Umożliwia dostęp do dowolnego obiektu z dowolnego miejsca poprzez korzeń drzewa.

## Zasady budowy klas

- Każda klasa posiada slot `_app` — referencja do korzenia drzewa (`App`).
- Każda klasa posiada metodę `init_<nazwa>()` — główny konstruktor inicjalizujący obiekt po jego utworzeniu.
- Konstruktor `__init__` tylko zeruje sloty do `None`; nie zawiera logiki inicjalizacyjnej.
- Obiekty podrzędne tworzone są lazy w property — property tworzy pusty obiekt z przekazanym `_app`.

## Nawigacja w drzewie

- Do góry: przez slot `_app` (zawsze dostępny).
- W dół: przez property z lazy loadingiem.
- Gdy klasa występuje jako element listy lub słownika, posiada dodatkowo slot z referencją do swojego bezpośredniego rodzica — adresacja w obie strony.

