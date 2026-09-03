"""Tracing bootstrap — instalacja generatora identyfikatorów korelacji.

Composition Root platformy ustawia adapter (infrastruktura) w port
``CorrelationIdGenerator`` (aplikacja) przez ambienny holder w
``application/context/correlation_id``. Dzięki temu mapper, outbox i logi
nigdy nie produkują pustego ``correlation_id``, a backend generowania jest
wymienialny przez DI.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.application.context import set_correlation_id_generator
from shell.platform.infrastructure.identity.uuid_correlation_id_generator import (
    UuidCorrelationIdGenerator,
)

if TYPE_CHECKING:
    from shell.platform.application.context.ports.correlation_id_generator import (
        CorrelationIdGenerator,
    )


def install_trace_id_generator(generator: CorrelationIdGenerator | None = None) -> None:
    """Instaluje generator identyfikatorów korelacji w holderze kontekstu.

    Wywoływane raz, na starcie procesu (HTTP server i/lub worker). Gdy
    ``generator`` nie jest podany, domyślnie używa ``UuidCorrelationIdGenerator``.
    """
    set_correlation_id_generator(generator or UuidCorrelationIdGenerator())
