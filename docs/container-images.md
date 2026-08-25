# Obrazy kontenerowe SHELL

## Po co jest ten dokument

Ten dokument jest krótką informacją dla człowieka o obrazach opublikowanych w GitHub Container Registry (GHCR). Nie zastępuje workflow CI/CD:

- workflow definiuje, jak obraz jest budowany, testowany i publikowany;
- ten dokument opisuje, jakie obrazy i tagi faktycznie są dostępne;
- źródłem prawdy dla zawartości obrazu pozostaje konkretny digest OCI zwrócony przez rejestr.

Nie należy dodawać informacji o GHCR do każdego pliku domenowego, kontenera DI ani adaptera. Obraz jest artefaktem wdrożeniowym, więc jego dokumentacja należy do `docs/` i workflow wdrożeniowych.

## Rejestr

Obrazy są przechowywane w namespace:

```text
ghcr.io/wiejskilopez/shell/
```

Dostępne usługi:

| Usługa | Obraz |
|---|---|
| Definition | `ghcr.io/wiejskilopez/shell/shell-definition-service` |
| Execution | `ghcr.io/wiejskilopez/shell/shell-execution-service` |
| Ingestion | `ghcr.io/wiejskilopez/shell/shell-ingestion-service` |
| Project | `ghcr.io/wiejskilopez/shell/shell-project-service` |
| Scheduling | `ghcr.io/wiejskilopez/shell/shell-scheduling-service` |
| Session | `ghcr.io/wiejskilopez/shell/shell-session-service` |
| User | `ghcr.io/wiejskilopez/shell/shell-user-service` |

## Aktualnie opublikowane tagi

Stan zweryfikowany po publikacji lokalnej: **2026-08-25**.

Każdy z siedmiu obrazów ma obecnie tagi:

```text
0.1.0
local-863723a9
```

Tag `0.1.0` jest tagiem wersji pakietu. Tag `local-863723a9` identyfikuje build wykonany lokalnie na podstawie skrótu bieżącego `HEAD`.

Ponieważ w momencie publikacji repozytorium zawierało niezatwierdzone zmiany, tag `local-863723a9` należy traktować jako artefakt testowy, a nie jako podpisany release produkcyjny. Przed produkcyjnym wdrożeniem obraz powinien zostać zbudowany z czystego commita i opublikowany z tagiem odpowiadającym temu commitowi.

## Pobieranie obrazu

Przykład:

```powershell
docker pull ghcr.io/wiejskilopez/shell/shell-user-service:0.1.0
docker pull ghcr.io/wiejskilopez/shell/shell-session-service:0.1.0
```

Dla pozostałych usług należy użyć nazw z tabeli i tego samego tagu.

## Weryfikacja lokalna

Sprawdzenie dostępności tagu:

```powershell
docker manifest inspect ghcr.io/wiejskilopez/shell/shell-user-service:0.1.0
docker manifest inspect ghcr.io/wiejskilopez/shell/shell-session-service:0.1.0
```

Lokalny test obrazu, obejmujący brokera, API, workera oraz przejście readiness `503 -> 200`, wykonuje:

```powershell
python -m scripts.verify_user_service_image --image shell-user-service:0.1.0 --service user
python -m scripts.verify_user_service_image --image shell-session-service:0.1.0 --service session
```

Workflowy związane z publikacją:

- `.github/workflows/user-service.yml`;
- `.github/workflows/session-service.yml`;
- `.github/workflows/remaining-services.yml`.

## Publikacja

Publikacja do GHCR wymaga zalogowania Dockera:

```powershell
docker login ghcr.io
```

Produkcja nie powinna używać tagu `latest`. Zalecane są jednocześnie:

- niezmienny tag obrazu oparty na SHA commita;
- tag wersji semantycznej, gdy jest to formalny release;
- digest OCI zapisany w systemie wdrożeniowym.

Workflow publikuje obrazy z wersją i SHA przy release tagowanym w GitHub. Lokalna publikacja nie oznacza automatycznie, że kod repozytorium został commitowany lub wypchnięty do GitHub.

## Stan dodatkowego tagu diagnostycznego

Podczas pierwszej próby konfiguracji został utworzony dodatkowy tag `diagnostic` dla obrazu User. Próba usunięcia go przez GitHub Packages API zwróciła `404`, dlatego jego obecność należy sprawdzić bezpośrednio w pakiecie GHCR. Nie jest on używany przez workflow ani przez dokumentowane wdrożenia.
