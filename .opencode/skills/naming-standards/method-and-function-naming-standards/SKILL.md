---
name: method-and-function-naming-standards
description: Reguły nazewnictwa metod i funkcji — snake_case, intencja biznesowa, konwencje dla agregatów, repozytoriów, factory, handlerów.
---

# Method and Function Naming Standards

> Reguły nazewnictwa metod i funkcji we wszystkich warstwach projektu.

## Podstawowa zasada

- Wszystkie metody i funkcje: `snake_case`
- Wyrażają **intencję biznesową**; operacja techniczna pozostaje poza nazwą metody.

```python
# POPRAWNIE — intencja biznesowa
order.confirm()
workflow.mark_completed()
task.assign_to(user)
invoice.cancel()

# ŹLE — operacja techniczna
order.save()
workflow.update()
task.merge()
invoice.set_status()
aggregate.persist()
```

## Metody na agregatach

Każda metoda domenowa na agregacie:
- Wyraża intencję biznesową
- Woła `append_event()` z odpowiednim DomainEvent
- Zawiera guard clause na początku (sprawdza invarianty)

```python
def start_at(self, now: datetime) -> None:
    if self._status != Status.idle():
        raise InvalidStateTransition(...)
    self._status = Status.running()
    self.append_event(WorkflowStartedEvent.now(self.id, now=now))

def finish(self, *, now, task_execution_id=None) -> None:
    self._status = Status.done()
    self.append_event(WorkflowCompletedEvent.now(self.id, task_execution_id, now=now))
```

## Metody repozytorium

Repository to **element techniczny** (warstwa infrastruktury), dlatego metody repozytorium używają standardowych, technicznych nazw — nie wymagają nazw biznesowych.

```python
# POPRAWNIE — konwencja nazewnicza (techniczna):
get_by_id(id)        # zwraca 1 agregat lub None
save(aggregate)      # zapisuje nowy lub aktualizuje (metoda: save)
delete(id)           # usuwa agregat (metoda: delete)
list_by_*(...)       # zwraca listę
find_latest_by_*(...) # zwraca najnowszy
exists(id)           # zwraca bool
```

**UWAGA:** Metoda zapisu nosi nazwę `save()` (bez wariantów `store()`, `persist()`, `add()`, `update()`).

## Metody factory

Nazwy factory method powinny dokumentować intencję:

| Metoda | Zastosowanie |
|--------|-------------|
| `of(data)` | Tworzy z surowych danych (z obliczeniami) |
| `from_hex(hex_str)` | Tworzy z gotowego formatu |
| `from_string(value)` | Parsuje z stringa |
| `now()` | Bieżący czas / timestamp |
| `initial()` | Wartość początkowa (np. Version 1) |
| `default()` | Wartość domyślna |
| `generate()` | Generuje nowy identyfikator |
| `yes()` / `no()` | Dla boolowskich VO |

```python
@classmethod
def initial(cls) -> Version:
    return cls(1)

@classmethod
def now(cls) -> Timestamp:
    return cls(datetime.now(tz=UTC))

@classmethod
def generate(cls) -> GraphDefinitionId:
    return cls(str(uuid4()))
```

## Metody query service

```python
get_by_id(id) → Dto | None
get_by_*(...) → Dto | None
list_by_*(...) → list[Dto]
search(query) → list[Dto]
```

## Handler methods

Jedyna publiczna metoda handlera:

```python
async def handle(self, command: SomeCommand) -> None: ...
async def handle(self, query: SomeQuery) -> list[Dto]: ...
async def handle(self, event: SomeEvent) -> None: ...
```

## Metody zwracające kolekcje

Property/metody zwracające kolekcje powinny sugerować typ zwracany:

```python
@property
def items(self) -> tuple[OrderItem, ...]: ...

@property
def metadata(self) -> dict[str, str]: ...
```
