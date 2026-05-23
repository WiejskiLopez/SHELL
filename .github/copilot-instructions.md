# Python coding conventions

## Kontekst projektu

Piszemy w Pythonie prosty system agentowy.

**Platforma:** `C:\Users\palysiewicz\IdeaProjects\MICROSYSTEM\.github\copilot-knowledge\07-automation\platform`

**Tasker** — executor który na podstawie pliku opisu taska i pliku graph generuje strukturę katalogów potrzebną do inicjalizacji wszystkich node'ów taska.
- Przykład opisu taska: `..\tasker\default-tasker\examples\my-task.md`
- Przykład graph: `..\tasker\default-tasker\examples\my-task.yaml`

---

## Zasady ogólne

- Nie dodawaj komentarzy do metod Pythona, a istniejace usuwaj.
- Nie dodawaj komentarz do klas a istniejace usun
- Importy zawsze na górze pliku, nigdy wewnątrz metod.
- Nie używaj skrótów w nazwach zmiennych — pełne nazwy opisowe.

---

## Sloty i properties

- Sloty są zmiennymi prywatnymi z `_` na początku. Dostęp z zewnątrz klasy tylko przez property z sufiksem `_`.
- Nie twórz proxy property bez dodatkowej walidacji — używaj bezpośrednio.
- Nigdy nie odwołuj się do slotu wprost (`_nazwa`) — zawsze przez property (`nazwa_`).

---

## Walidacja slotów

- Slot wymagany: utwórz `_assert_<nazwa>.py` w `internal/` i wywołaj w property. Nigdy `if ... raise` inline w property.
- Slot opcjonalny: zaznacz `Optional` w docstringu klasy, nie waliduj obecności.

---

## Nagłówek klasy

Docstring klasy zawiera sekcję `Slots:` z nazwami pól; opcjonalne oznaczone `Optional`:

```
Slots:
    _app      — parent App
    _dry_run  — Optional; True if --dry-run flag set
```

---

## Inicjalizacja klas

- Konstruktor (`__init__`) tylko zeruje sloty do `None` lub wartości domyślnych — nie zawiera logiki inicjalizacyjnej, nie tworzy obiektów podrzędnych.
- Obiekty podrzędne tworzone są **lazy w property** — property tylko tworzy instancję, nie inicjalizuje jej.
- Logika inicjalizacji idzie do `_init_<nazwa>.py` w `internal/`, wywoływanej przez publiczną metodę `init_<nazwa>()`. Funkcja `_init_*` korzysta z property (nie ze slotu bezpośrednio):

  ```python
  @property
  def foo_(self) -> Foo:
      if self._foo is None:
          self._foo = Foo()
      return self._foo

  def init_foo(self) -> None:
      _init_foo(self)

  # internal/_init_foo.py
  def _init_foo(obj: 'MyClass') -> None:
      obj.foo_.init_foo_bar(obj.bar_)
  ```

- Każda metoda publiczna klasy, która inicjalizuje slot lub sloty, **musi** nazywać się `init_<nazwa>()`. Inne nazwy (np. `build_*`, `create_*`, `setup_*`) są niedozwolone. To samo dotyczy prywatnych funkcji w `internal/` — muszą to być `_init_<nazwa>.py`.
- Nazwy metod publicznych muszą mieć pełną formę: `<akcja>_<na_czym>`, np. `clean_node_input`, `init_node_temp`. Nie używaj skrótów: `clean_input` jest niedozwolone, `clean_node_input` jest poprawne.
- Funkcja wewnętrzna w `internal/` musi mieć nazwę identyczną z metodą publiczną, poprzedzoną `_`, np. metoda `clean_node_temp` → plik `internal/_clean_node_temp.py`, funkcja `_clean_node_temp`.

---

## Klasa Node — dwa konteksty

Klasa `Node` jest używana w dwóch kontekstach. W obu `node_dir` jest przekazywany z zewnątrz.

**AppNode:** `node_dir` z CLI (`--node-dir`) lub fallback `runner_root_dir / ".node"`, inicjalizacja przez `_init_app_node(app)`

**GraphNode:** `node_dir` = `app.app_node_.node_.node_dir_ / node_name`, `node_name` z `graph.yaml`, inicjalizacja przez `_init_graph_node(graph_node, ...)`

---

## Wzorce i konwencje

- Przed napisaniem nowego kodu — przeszukaj istniejący kod i trzymaj się wzorców.
- Jeśli uważasz, że wzorzec jest błędny — zapytaj programistę przed zmianą.

---

## Komentarze i docstringi

Minimalistyczne — tylko to, czego nie da się wywnioskować z kodu.

---

## Operacje na plikach i katalogach

Do wszystkich operacji na plikach i katalogach używamy **wyłącznie** klasy `UtilsPath` (`shell/utils_path/utils_path.py`). Bezpośrednie wywołania metod `Path` (np. `path.mkdir()`, `path.read_text()`) oraz modułów `shutil`, `os` są niedozwolone.

Dostępne metody: `mkdir`, `exists`, `is_file`, `is_dir`, `is_symlink`, `read_text`, `read_text_safe`, `write_text`, `unlink`, `rmtree`, `copy_to`, `move`, `iterdir`, `glob`, `rglob`.

---

## Obsługa błędów i trace

Każda akcja mogąca być źródłem błędu musi być otoczona wywołaniami `record_*` przed i po wykonaniu.


## Workflow Commands

**All commands:** [Workflow Commands Reference](copilot-knowledge/05-engineering/workflows/engineering_workflows_commands.md)

Dot commands (`.done`, `.clean`, `.format`, `.poc`) load and execute workflows automatically.

### `.done` — procedura zamknięcia sesji roboczej

Gdy użytkownik wpisze `.done` na chacie, wykonaj **dokładnie w tej kolejności**:

1. **`git add -A`** — stage wszystkich zmian w katalogu `platform/`
2. **`git commit`** — commit z automatycznym komunikatem opisującym zmiany z bieżącej sesji
3. **`git push`** — wypchnij branch na origin
4. **Utwórz nowy branch** — odczytaj numer z nazwy bieżącego brancha (format `<N>_feature`), zwiększ o 1, utwórz `<N+1>_feature` z `git checkout -b <N+1>_feature` i wypchnij `git push -u origin <N+1>_feature`
5. **Potwierdź** — wyświetl podsumowanie: nazwa commita, stary branch, nowy branch

Wszystkie komendy `git` uruchamiaj w katalogu `C:\Users\palysiewicz\IdeaProjects\schell\platform`.


Narazie w analizie pomijamy modul testowy