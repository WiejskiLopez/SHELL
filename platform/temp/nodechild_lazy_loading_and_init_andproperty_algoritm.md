# NodeLogs — wzorzec lazy loading, inicjalizacja, konstruktor, property, sloty

## Sloty

```python
__slots__ = ("_app", "_module_status")
```

- `_app` — referencja do parent App; przekazywana przez konstruktor
- `_module_status` — enum `ModuleStatus` (z `shell.module_status.module_status`); ustawiany w konstruktorze na `NEW`, zmieniany na `INIT` przez `init_node_logs()`

---

## Konstruktor

Konstruktor **tylko zeruje sloty** — bez logiki inicjalizacyjnej, bez tworzenia katalogów.

```python
def __init__(self, app) -> None:
    self._app = app
    self._module_status: ModuleStatus = ModuleStatus.NEW
```

- `app` — jedyny parametr; ścieżka **nie jest** przekazywana do konstruktora
- ścieżka `logs_dir` budowana jest **lazy w property** przez `_app`

---

## Property

### Ścieżka — budowana przez `_app`, nie slot

```python
@property
def node_logs_dir_(self) -> Path:
    return (self._app.app_node_.node_.node_dir_ / '.node' / 'logs').resolve()
```

Ścieżka nie jest trzymana jako slot — pobierana dynamicznie przez łańcuch `_app → app_node_ → node_ → node_dir_`.

### Status

```python
@property
def module_status_(self) -> ModuleStatus:
    return self._module_status
```

---

## Metoda inicjalizacyjna

```python
def init_node_logs(self) -> None:
    self._module_status = ModuleStatus.INIT
```

Wywoływana z `_init_node(node, ...)` po `node.node_input_.init_input()`.

---

## Lazy loading w klasie Node

```python
@property
def node_logs_(self) -> NodeLogs:
    if self._node_logs is None:
        self._node_logs = NodeLogs(self._app)
    return self._node_logs
```

- slot w `Node.__slots__`: `"_node_logs"`
- inicjalizacja w `__init__`: `self._node_logs = None  # NodeLogs, lazy`
- do konstruktora przekazywany **tylko `self._app`**, bez ścieżki

---

## Wywołanie init w `_init_node`

```python
node.node_input_.init_input()
node.node_logs_.init_node_logs()
```
