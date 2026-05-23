# Submoduł `app_node` — klasa `AppNode`

Łącznik między drzewem DOM aplikacji a strukturą katalogową node. Przechowuje uchwyt do głównego `Node` oraz zarządza blokadą na czas wykonania.

## Sloty

- `_app` — referencja do korzenia drzewa (`App`).
- `_node` — Optional; instancja `Node`; lazy.
- `_lock` — Optional; instancja `Locker`; lazy.

## Odpowiedzialność

- Jeden runtime przetwarza dane tylko swojego node — nie wykonuje zadań innych subnodów (może je wyłącznie uruchamiać, ale działają autonomicznie).
- `init_app_node()` — tworzy `Node` z argumentów CLI i struktury katalogu.
- Blokada (`lock_`) zakładana przez `_init_app_modules` na czas wykonania, zdejmowana po zakończeniu.
