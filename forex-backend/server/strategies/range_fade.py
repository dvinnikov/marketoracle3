from __future__ import annotations
from time import time
from ..core.models import Signal, Bar, Timeframe

class RangeFade:
    id = "range_fade"
    name = "Range Fade"
    description = "Fade edges of rolling window range"
    settingsSchema = {"lookback":{"type":"number","default":30,"min":10,"max":200},
                      "threshold":{"type":"number","default":0.75,"min":0.55,"max":0.95}}

    def on_init(self, ctx): self.ctx = ctx

    def on_bar(self, symbol: str, tf: Timeframe, bar: Bar):
        L = int(self.ctx.get_setting("lookback", 30))
        T = float(self.ctx.get_setting("threshold", 0.75))
        bars = self.ctx.get_bars(symbol, tf, L)
        if len(bars) < L: return []
        highs = max(b.h for b in bars)
        lows = min(b.l for b in bars)
        rng = highs - lows or 1e-9
        rel = (bar.c - lows) / rng
        side = "SELL" if rel > T else ("BUY" if rel < (1 - T) else None)
        if not side: return []
        return [Signal(
            id=f"{self.id}-{int(time())}",
            time=bar.t,
            symbol=symbol,
            strategy=self.id,
            side=side,
            entry=bar.c
        )]

def create():
    return RangeFade()
