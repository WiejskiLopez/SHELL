from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import WebSocket, WebSocketDisconnect

if TYPE_CHECKING:
    from shell.platform.application.bus.event_bus import EventBus


class SessionWebSocketHandler:
    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._connections: dict[str, list[WebSocket]] = {}

    async def handle(self, websocket: WebSocket, session_id: str) -> None:
        await websocket.accept()
        self._connections.setdefault(session_id, []).append(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            conns = self._connections.get(session_id, [])
            if websocket in conns:
                conns.remove(websocket)
            if not self._connections.get(session_id):
                del self._connections[session_id]

    async def broadcast(self, session_id: str, event: dict) -> None:
        for ws in list(self._connections.get(session_id, [])):
            try:
                await ws.send_json(event)
            except Exception:
                conns = self._connections.get(session_id, [])
                if ws in conns:
                    conns.remove(ws)
