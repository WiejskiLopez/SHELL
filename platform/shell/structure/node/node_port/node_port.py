"""node_port.py
NodePort — port (Protocol) abstrakcji storage dla operacji na nodzie.

Definiuje kontrakt wymienny między adapterami:
    - FilesystemNodePort  (domyślny, produkcyjny)
    - DbNodePort          (przyszłość: wszystkie operacje node → baza danych)
    - InMemoryNodePort    (testy: brak I/O)

Konwencja:
    PathType przekazywany do każdej metody jest logicznym identyfikatorem
    (np. node_dir / DIR_INPUT / 'task.md'), a nie bezwzględną ścieżką systemu plików.
    Adapter tłumaczy go na właściwe medium (ścieżka, klucz DB, klucz słownika).
"""

from __future__ import annotations

from shell.utils.path.path import Path, PathType
from typing import Protocol, runtime_checkable
from shell.constants.constants import DIR_INPUT


@runtime_checkable
class NodePort(Protocol):
    """Port definiujący wszystkie operacje I/O na strukturze node.

    Każda implementacja musi zapewnić pełną obsługę tych operacji
    dla swojego medium (filesystem, baza danych, pamięć itp.).
    """

    # -----------------------------------------------------------------------
    # Struktura katalogów / kontenerów
    # -----------------------------------------------------------------------

    def makedirs(self, path: PathType) -> None:
        """Utwórz katalog (wraz z rodzicami) lub odpowiednik w medium.

        Filesystem: path.mkdir(parents=True, exist_ok=True)
        DB:         INSERT INTO nodes(id, type) ON CONFLICT DO NOTHING
        """
        ...

    def exists(self, path: PathType) -> bool:
        """Sprawdź czy ścieżka / rekord istnieje."""
        ...

    def rmtree(self, path: PathType) -> None:
        """Usuń katalog rekurencyjnie lub wszystkie rekordy pod tym węzłem.

        Filesystem: shutil.rmtree(path, ignore_errors=True)
        DB:         DELETE FROM node_files WHERE path LIKE 'prefix%'
        """
        ...

    # -----------------------------------------------------------------------
    # Pliki / rekordy
    # -----------------------------------------------------------------------

    def read_text(self, path: PathType) -> str:
        """Odczytaj zawartość pliku lub rekordu jako tekst."""
        ...

    def write_text(self, path: PathType, content: str) -> None:
        """Zapisz tekst do pliku lub rekordu."""
        ...

    def unlink(self, path: PathType) -> None:
        """Usuń pojedynczy plik / rekord.

        Filesystem: path.unlink(missing_ok=True)
        DB:         DELETE FROM node_files WHERE path = ?
        """
        ...

    def list_files(self, path: PathType, suffix: str) -> list[PathType]:
        """Zwróć listę plików / rekordów w danym katalogu o podanym rozszerzeniu.

        Filesystem: sorted(path.glob(f'*{suffix}'))
        DB:         SELECT path FROM node_files WHERE parent = ? AND suffix = ?
        """
        ...

    def move(self, src: PathType, dst: PathType) -> None:
        """Przenieś plik / rekord z src do dst.

        Filesystem: shutil.move(src, dst)
        DB:         UPDATE node_files SET path = ? WHERE path = ?
        """
        ...
