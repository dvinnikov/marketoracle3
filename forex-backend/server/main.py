from __future__ import annotations
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from .api.rest import router as rest_router
from .api.bridge import router as bridge_router
from .api.commands import router as commands_router
from .api.udf import router as udf_router
from .core.ws import WS_HUB
from .config import settings

app = FastAPI(title="Forex Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rest_router)
app.include_router(bridge_router)
app.include_router(commands_router)
app.include_router(udf_router)

@app.websocket("/ws/market")
async def ws_market(ws: WebSocket):
    await WS_HUB.register(ws)
    try:
        while True:
            await ws.receive_text()  # keepalive / ignore
    except Exception:
        pass
    finally:
        WS_HUB.unregister(ws)

def create_app():
    return app
