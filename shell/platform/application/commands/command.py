"""Command — korzeń tożsamości wszystkich komend aplikacyjnych.

Każda komenda SHELL posiada ``command_id`` nadawany AUTOMATYCZNIE w chwili
konstrukcji (``default_factory``). Tożsamość jest niezmiennicza i bezwzględna:

- tworzenie: id generowane w tle, bez udziału wywołującego;
- kopiowanie (``dataclasses.replace``): id jest zachowywane (pole przenoszone);
- deserializacja z payload/JSON: pole ``command_id`` jest oznaczone w
  ``metadata`` kluczem ``PAYLOAD_REQUIRED_KEY`` jako WYMAGANE — brak id w
  payload = błąd, nigdy nie jest ono nadawane na nowo po wejściu komendy
  w obieg (tracing/dedup nie mogą stracić tożsamości na hopie).

Klasa pozostaje bazą wyłącznie znacznikowo-typującą: poza polem ``command_id``
i walidacją jego niepustości nie niesie żadnej logiki. Umożliwia infrastrukturze
(dyspozytor delivery, relay, inbox, serializacja) traktowania każdej komendy jako
obiektu z tożsamością, bez znajomości konkretnego typu komendy.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

PAYLOAD_REQUIRED_KEY = "shell.payload_required"


def _new_command_id() -> str:
    return str(uuid.uuid4())


@dataclass(frozen=True, slots=True)
class Command:
    """Wspólna baza komend: automatyczna, obowiązkowa tożsamość."""

    command_id: str = field(
        default_factory=_new_command_id,
        kw_only=True,
        metadata={PAYLOAD_REQUIRED_KEY: True},
    )

    def __post_init__(self) -> None:
        if not self.command_id:
            raise ValueError("command_id cannot be empty")