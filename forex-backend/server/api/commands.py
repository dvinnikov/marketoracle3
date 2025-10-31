from __future__ import annotations
from fastapi import APIRouter, Body
from pydantic import BaseModel
from typing import Literal

router = APIRouter()
_COMMANDS: list[dict] = []
_LAST_ID = 0

def _next_id() -> int:
    global _LAST_ID
    _LAST_ID += 1
    return _LAST_ID

class MarketCmd(BaseModel):
    symbol: str
    side: Literal["buy","sell"]
    volume: float
    sl: float | None = None
    tp: float | None = None

@router.post("/api/commands/market")
def api_market(c: MarketCmd):
    cmd = {"id": _next_id(), "type":"market", **c.model_dump()}
    _COMMANDS.append(cmd)
    return {"ok": True, "id": cmd["id"]}

class ModifyCmd(BaseModel):
    ticket: int
    sl: float | None = None
    tp: float | None = None

@router.post("/api/commands/modify")
def api_modify(c: ModifyCmd):
    cmd = {"id": _next_id(), "type":"modify", **c.model_dump()}
    _COMMANDS.append(cmd)
    return {"ok": True, "id": cmd["id"]}

class CloseCmd(BaseModel):
    ticket: int

@router.post("/api/commands/close")
def api_close(c: CloseCmd):
    cmd = {"id": _next_id(), "type":"close", **c.model_dump()}
    _COMMANDS.append(cmd)
    return {"ok": True, "id": cmd["id"]}

# --- EA bridge side ---

@router.post("/bridge/commands/fetch")
def bridge_fetch(payload: dict = Body(...)):
    after = int(payload.get("after", 0))
    out = [c for c in _COMMANDS if c["id"] > after]
    return {"commands": out}

@router.post("/bridge/commands/ack")
def bridge_ack(payload: dict = Body(...)):
    # In-memory ack: no deletion to keep history; prod could mark delivered.
    return {"ok": True, "id": payload.get("id"), "ack": True}
