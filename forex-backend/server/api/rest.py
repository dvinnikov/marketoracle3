from __future__ import annotations
from fastapi import APIRouter, Query
from pydantic import BaseModel
from ..core.state import STATE
from ..core.loader import StrategyLoader
from ..core.orchestrator import ORCH
from ..core.prediction import predict
from ..core.storage import list_signals
from ..core.models import Signal
from ..config import settings

router = APIRouter()

_loader = StrategyLoader(settings.STRATEGIES_DIR)
_loader.discover()

@router.get("/healthz")
def healthz():
    return {"ok": True, "ticks": len(STATE.ticks), "symbols": len(STATE.instruments), "status": STATE.status}

@router.get("/api/instruments")
def api_instruments():
    return {"symbols": STATE.instruments or [{"symbol":"EURUSD","digits":5,"point":0.00010}]}

@router.get("/api/candles")
def api_candles(symbol: str, timeframe: int = 60, limit: int = 300):
    dq = STATE.bars.get((symbol, timeframe), [])
    bars = [b.__dict__ for b in list(dq)[-limit:]]
    return {"bars": bars}

@router.get("/api/strategies")
def api_strategies():
    return _loader.discover()

class EnablePayload(BaseModel):
    id: str
    symbol: str
    tf: int
    settings: dict = {}

@router.post("/api/strategies/enable")
def api_strat_enable(payload: EnablePayload):
    inst = _loader.load(payload.id)
    ORCH.enable(payload.id, inst, payload.symbol, int(payload.tf), payload.settings)
    return {"ok": True}

class DisablePayload(BaseModel):
    id: str
    symbol: str
    tf: int

@router.post("/api/strategies/disable")
def api_strat_disable(payload: DisablePayload):
    ORCH.disable(payload.id, payload.symbol, int(payload.tf))
    return {"ok": True}

@router.get("/api/signals")
def api_signals(symbol: str | None = Query(None), limit: int = 200):
    items = [s.__dict__ for s in list_signals(symbol, limit=limit)]
    return {"items": items}

@router.get("/api/prediction")
def api_prediction(symbol: str, tf: int):
    p = predict(symbol, tf)
    return p.__dict__
