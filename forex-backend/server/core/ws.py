from __future__ import annotations
from typing import Any, Set
from fastapi import WebSocket

class WebSocketHub:
    def __init__(self) -> None:
        self.clients: Set[WebSocket] = set()

    async def register(self, ws: WebSocket) -> None:
        await ws.accept()
        self.clients.add(ws)

    def unregister(self, ws: WebSocket) -> None:
        self.clients.discard(ws)

    async def broadcast(self, topic: str, data: Any) -> None:
        dead = []
        for ws in list(self.clients):
            try:
                await ws.send_json({"topic": topic, "data": data})
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.unregister(ws)

WS_HUB = WebSocketHub()
