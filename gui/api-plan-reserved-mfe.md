# Reserved MFE — plan API

## Opis
Mikrofrontend prawej kolumny (22% szerokości). Obecnie zarezerwowana na przyszłe funkcje — nie ma konkretnych wymagań API.

---

## 1. Potencjalne przyszłe funkcje

Zgodnie z `opis gui.txt`, prawa kolumna jest przewidziana pod:
- Podgląd plików (artifactów)
- Metadane taska
- Inspektor kodu
- Dodatkowe dane kontekstowe

## 2. Potencjalne endpointy w przyszłości

| Endpoint | Potencjalne zastosowanie |
|---|---|
| `GET /api/v1/node-executions/{id}/artifacts` | Lista plików/artifactów wygenerowanych przez node |
| `GET /api/v1/task-executions/{id}/metadata` | Metadane / szczegółowe info o tasku |
| `GET /api/v1/files/{file_id}` | Pobranie zawartości pliku (artifact) |

## 3. Stan backendu

| Endpoint | Status |
|---|---|
| Obsługa artifactów | ✗ Brak |
| endpointy metadata | ✗ Brak |

## 4. Co trzeba zbudować

Nic na razie — prawa kolumna jest pusta i nie blokuje MVP. Wrócić do tego w późniejszej iteracji.
