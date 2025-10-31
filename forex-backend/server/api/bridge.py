from __future__ import annotations
from fastapi import APIRouter, Body
from ..core.models import Tick, Account, Position, Order
from ..core.state import STATE
from ..core.bars import BarAggregator
from ..core.orchestrator import ORCH
from ..core.ws import WS_HUB
from ..config import settings
from ..core.prediction import predict

router = APIRouter(prefix="/bridge", tags=["bridge"])
_agg = BarAggregator(lambda s,tf,b: ORCH.on_bar(s,tf,b))

@router.post("/tick")
async def tick(payload: dict = Body(...)):
    t = Tick(symbol=payload["symbol"], bid=float(payload["bid"]), ask=float(payload["ask"]), time=int(payload["time"]))
    STATE.ticks[t.symbol] = t
    await WS_HUB.broadcast("price.tick", t.__dict__)
    # build/roll bars and broadcast live updates
    for (sym, tf, bar) in _agg.ingest_tick(t.symbol, t, settings.AGG_TF):
        await WS_HUB.broadcast("bar.update", {"symbol": sym, "tf": tf, "bar": bar.__dict__})
    return {"ok": True}

@router.post("/account")
async def account(payload: dict = Body(...)):
    STATE.account = Account(**payload)
    return {"ok": True}

@router.post("/positions")
async def positions(payload: dict = Body(...)):
    items = payload.get("positions", [])
    STATE.positions = [Position(**x) for x in items]
    return {"ok": True, "count": len(STATE.positions)}

@router.post("/orders")
async def orders(payload: dict = Body(...)):
    items = payload.get("orders", [])
    STATE.orders = [Order(**x) for x in items]
    return {"ok": True, "count": len(STATE.orders)}

@router.post("/instruments")
async def instruments(payload: dict = Body(...)):
    STATE.instruments = payload.get("symbols", [])
    return {"ok": True, "count": len(STATE.instruments)}

@router.post("/status")
def status(payload: dict = Body(...)):
    STATE.status = payload.get("status", "running")
    return {"ok": True, "status": STATE.status}
