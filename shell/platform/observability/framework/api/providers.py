"""ObservabilityProviders — jawny zestaw providów obserwowalności kontenera.

Framework (``install_metrics`` / ``mount_readiness``) nie powinien znać
wewnętrznej struktury kontenera DI ani używać dynamicznego ``getattr`` na
nazwie string (ciche pominięcie przy literówce). Zamiast tego fabryka aplikacji
BC buduje ten frozen bundle i przekazuje go do frameworku: brak wymaganego
providu to twardy ``AttributeError`` w momencie ``from_container``, a nie
cichy brak endpointu.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ObservabilityProviders:
    """Providery obserwowalności wyekstrahowane z kontenera DI.

    ``metrics_exporter`` i ``readiness_probe`` są wymagane — ich brak kończy
    się twardym błędem ``AttributeError`` w ``from_container``.
    ``inbox_metrics_service``/``outbox_metrics_service`` są opcjonalne (BC bez
    delivery pomija odświeżanie snapshotów — wartość ``None``).
    """

    metrics_exporter: Any
    readiness_probe: Any
    inbox_metrics_service: Any = None
    outbox_metrics_service: Any = None

    @classmethod
    def from_container(cls, container: object) -> ObservabilityProviders:
        """Wymagane providy czytane bezpośrednio (twardy błąd), opcjonalne z ``None``.

        Dostęp przez jawną nazwę atrybutu gwarantuje, że literówka w nazwie
        providu w kontenerze przestaje być cichym pominięciem endpointu.
        """
        return cls(
            metrics_exporter=container.metrics_exporter,  # type: ignore[attr-defined]
            readiness_probe=container.readiness_probe,  # type: ignore[attr-defined]
            inbox_metrics_service=getattr(container, "inbox_metrics_service", None),
            outbox_metrics_service=getattr(container, "outbox_metrics_service", None),
        )
