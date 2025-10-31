from __future__ import annotations
from time import time
from server.core.models import Signal, Bar, Timeframe

def is_bull_pin(b: Bar) -> bool:
    body = abs(b.c - b.o); upper = b.h - max(b.c, b.o); lower = min(b.c, b.o) - b.l
    return lower > body * 2 and upper < body and b.c > b.o

def is_bear_pin(b: Bar) -> bool:
    body = abs(b.c - b.o); upper = b.h - max(b.c, b.o); lower = min(b.c, b.o) - b.l
    return upper > body * 2 and lower < body and b.c < b.o

class PriceAction:
    id = "price_action"
    name = "Price Action"
    description = "Pin bar reversal at recent swing extremes."
    settingsSchema = {
        "swing_lookback": {"type":"number","default": 8, "min": 3, "max": 40},
        "rr": {"type":"number","default": 2.0}
    }

    def on_init(self, ctx): self.ctx = ctx

    def on_bar(self, symbol: str, tf: Timeframe, bar: Bar):
        lb = int(self.ctx.get_setting("swing_lookback", 8))
        rr = float(self.ctx.get_setting("rr", 2.0))
        bars = self.ctx.get_bars(symbol, tf, lb+5)
        if len(bars) < lb+2: return []
        curr = bars[-1]
        window = bars[-(lb+1):-1]
        hi = max(b.h for b in window)
        lo = min(b.l for b in window)

        out = []
        if is_bull_pin(curr) and curr.l <= lo:
            entry = curr.c; sl = curr.l; tp = entry + (entry - sl) * rr
            out.append(Signal(id=f"{self.id}-{int(time())}", time=curr.t, symbol=symbol,
                              strategy=self.id, side="BUY", entry=entry, sl=sl, tp=tp,
                              note="Bullish pin at swing low"))
        if is_bear_pin(curr) and curr.h >= hi:
            entry = curr.c; sl = curr.h; tp = entry - (sl - entry) * rr
            out.append(Signal(id=f"{self.id}-{int(time())}", time=curr.t, symbol=symbol,
                              strategy=self.id, side="SELL", entry=entry, sl=sl, tp=tp,
                              note="Bearish pin at swing high"))
        return out

def create(): return PriceAction()
