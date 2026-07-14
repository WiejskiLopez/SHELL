# JSON Serialization Convention — Domain VO ↔ Persistence Column

## Problem

Domain VOs wrapping `JsonStr` (e.g., `StateData`, `SkillData`) hold data as a JSON
**string**.  SQLAlchemy JSONB columns (`Mapped[dict]`) expect a Python **dict**.
The conversion between these two representations often uses an unsafe or redundant
`json.dumps(json.loads(X))` roundtrip.

## Reguły

### 1. Write direction (entity → model) — `json.loads()`

```python
# DOBRZE — produkuje dict dla JSONB kolumny
model.state_data = json.loads(entity.state_data.value.value)
```

```python
# ŹLE — json.dumps(json.loads(...)) to niepotrzebny roundtrip
model.state_data = json.dumps(json.loads(entity.state_data.value.value))  # type: ignore[assignment]

# ŹLE — przypisanie VO zamiast dict
model.state_data = entity.state_data  # type: ignore[assignment]
```

Łańcuch typów: `StateData` → `.value` → `JsonStr` → `.value` → `str` → `json.loads()` → `dict`

### 2. Read direction (model → entity) — `json.dumps()`

```python
# DOBRZE — konwertuje dict z JSONB kolumny na str dla JsonStr
state_data=StateData(JsonStr(json.dumps(dict(model.state_data)))),
```

Łańcuch typów: `dict` (z JSONB kolumny) → `json.dumps()` → `str` → `JsonStr()` → wrap → `StateData()`

### 3. Brak `# type: ignore[assignment]`

Po zastosowaniu reguły 1 nie ma już type mismatch: `json.loads()` zwraca `dict`,
a kolumna to `Mapped[dict]`.  Nie dodawaj `# type: ignore[assignment]`.

## Test weryfikacji

```python
# Write direction
data_str = '{"key": "value"}'
vo = StateData(JsonStr(data_str))
result = json.loads(vo.value.value)       # → dict
assert isinstance(result, dict)

# Read direction (model → entity)
db_dict = {"key": "value"}
result = StateData(JsonStr(json.dumps(dict(db_dict))))
assert isinstance(result, StateData)
```

## Dodatkowe zasoby

- `shell/platform/domain/value_objects/state_data.py` — `StateData(ValueObject)`
- `shell/platform/types/` — `JsonStr` definicja
- Wszystkie VOs z `value: JsonStr` (SkillData, ProjectSkillData, StateData, itp.)
