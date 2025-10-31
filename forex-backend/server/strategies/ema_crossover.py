from __future__ import annotations
from time import time
from ..core.models import Signal, Bar, Timeframe
from ..core.indicators import ema

class EmaCrossover:
    id = "ema_crossover"
    name = "EMA Crossover"
    description = "Fast/Slow EMA cross on close"
    settingsSchema = {"fast":{"type":"number","default":9,"min":2,"max":50},
                      "slow":{"type":"number","default":21,"min":5,"max":200}}

    def on_init(self, ctx): self.ctx = ctx

    def on_bar(self, symbol: str, tf: Timeframe, bar: Bar):
        bars = self.ctx.get_bars(symbol, tf, 300)
        closes = [b.c for b in bars]
        if len(closes) < 50: return []
        f = int(self.ctx.get_setting("fast", 9))
        s = int(self.ctx.get_setting("slow", 21))
        fast = ema(closes, f)
        slow = ema(closes, s)
        if fast != fast or slow != slow:  # NaN check
            return []
        side = "BUY" if fast > slow else "SELL"
        return [Signal(
            id=f"{self.id}-{int(time())}",
            time=bar.t,
            symbol=symbol,
            strategy=self.id,
            side=side,
            entry=bar.c
        )]

def create():
    return EmaCrossover()
