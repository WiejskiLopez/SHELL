"""Obsługa WebSocket dla strumieni sesji — KONCEPCJA FUTURE (nieaktywna).

Status: planowany (future concept), nie podłączony produkcyjnie.
Brak rejestracji jakiejkolwiek trasy WebSocket w aplikacjach BC
(``app.websocket`` / ``add_api_websocket_route``), brak instancji tego handlera
w composition root oraz brak testów. Klasse utrzymujemy jako propozycję
pod przyszły sygnał czasu rzeczywistego (np. push eventów sesji do klienta).

Decyzja techniczna: jeżeli koncept nie zostanie wdrożony w rozsądnym
horyzoncie i stanie się martwym kodem legacy (nieużywana, nieprzetestowana
abstrakcja), NALEŻY go przebudować/uwzględnić w architekturze, a nie
utrzymywać bezczynnie. Domniemanie: aktywny WebSocket wymaga osobnego
kontraktu i middleware'a (transport dwukierunkowy, inny niż HTTP), patrz
notatki o observability w conversacji projektowej.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from fastapi import WebSocket, WebSocketDisconnect

if TYPE_CHECKING:
    from shell.platform.application.bus.event_bus import EventBus

logger = logging.getLogger(__name__)


class SessionWebSocketHandler:
    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._connections: dict[str, list[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def handle(self, websocket: WebSocket, session_id: str) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.setdefault(session_id, []).append(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            async with self._lock:
                conns = self._connections.get(session_id, [])
                if websocket in conns:
                    conns.remove(websocket)
                if not self._connections.get(session_id):
                    del self._connections[session_id]

    async def broadcast(self, session_id: str, event: dict[str, object]) -> None:
        async with self._lock:
            peers = list(self._connections.get(session_id, []))
        for ws in peers:
            try:
                await ws.send_json(event)
            except Exception:
                logger.warning("websocket send failed for session %s; removing peer", session_id)
                async with self._lock:
                    conns = self._connections.get(session_id, [])
                    if ws in conns:
                        conns.remove(ws)
