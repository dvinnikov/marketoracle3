from __future__ import annotations
from .state import STATE
from .models import Prediction, Timeframe

def predict(symbol: str, tf: Timeframe) -> Prediction:
    dq = STATE.bars.get((symbol, tf))
    if not dq or len(dq) < 2:
        return Prediction(symbol=symbol, tf=tf, target=None, confidence=None)
    last = dq[-1]
    prev = dq[-2]
    slope = last.c - prev.c
    target = last.c + slope * 3
    conf = min(0.95, max(0.05, abs(slope) * 100))
    return Prediction(symbol=symbol, tf=tf, target=round(target, 5), confidence=round(conf, 2))
