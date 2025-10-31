from __future__ import annotations
from fastapi import APIRouter, Query
from ..core.state import STATE

router = APIRouter(prefix="/udf", tags=["udf"])

@router.get("/symbols")
def symbols(symbol: str):
    # minimal response compatible with TV datafeed queries
    return {
        "name": symbol,
        "ticker": symbol,
        "type": "forex",
        "session": "24x7",
        "timezone": "Etc/UTC",
        "exchange": "MT5",
        "minmov": 1,
        "pricescale": 100000,
        "has_daily": True,
        "has_intraday": True,
        "supported_resolutions": ["1","5","15","60","240","1D"]
    }

@router.get("/history")
def history(symbol: str, resolution: str, _from: int = Query(..., alias="from"), to: int = Query(...)):
    tf_map = {"1":1, "5":5, "15":15, "60":60, "240":240, "1D":1440}
    tf = tf_map.get(resolution, 60)
    dq = STATE.bars.get((symbol, tf), [])
    bars = [b for b in dq if _from <= b.t <= to]
    if not bars:
        return {"s":"no_data","t":[],"o":[],"h":[],"l":[],"c":[],"v":[]}
    return {"s":"ok",
            "t":[b.t for b in bars],
            "o":[b.o for b in bars],
            "h":[b.h for b in bars],
            "l":[b.l for b in bars],
            "c":[b.c for b in bars],
            "v":[b.v or 0 for b in bars]}
