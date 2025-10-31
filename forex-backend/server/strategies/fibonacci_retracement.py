from __future__ import annotations
from time import time
from server.core.models import Signal, Bar, Timeframe

FIBS = [0.236, 0.382, 0.5, 0.618, 0.786]

class FibonacciRetracement:
    id = "fibonacci_retracement"
    name = "Fibonacci Retracement"
    description = "Pullback entries at key Fibonacci levels after swing."
    settingsSchema = {
        "swing_len": {"type":"number","default": 30, "min": 10, "max": 400},
        "level": {"type":"number","default": 0.618},
        "sl_buffer": {"type":"number","default": 0.0010},
        "tp_rr": {"type":"number","default": 2.0},
        "lookback": {"type":"number","default": 400}
    }

    def on_init(self, ctx): self.ctx = ctx

    def on_bar(self, symbol: str, tf: Timeframe, bar: Bar):
        L = int(self.ctx.get_setting("swing_len", 30))
        level = float(self.ctx.get_setting("level", 0.618))
        sl_buf = float(self.ctx.get_setting("sl_buffer", 0.0010))
        rr = float(self.ctx.get_setting("tp_rr", 2.0))
        look = int(self.ctx.get_setting("lookback", 400))

        bars = self.ctx.get_bars(symbol, tf, look)
        if len(bars) < L + 2: return []
        curr = bars[-1]
        sw = bars[-(L+1):-1]
        hi = max(sw, key=lambda b: b.h).h
        lo = min(sw, key=lambda b: b.l).l

        if hi - lo <= 0: return []
        # Determine direction by last swing close
        long_trend = sw[-1].c > sw[0].c

        out = []
        if long_trend:
            fib = hi - (hi - lo) * level
            # if price tests around fib and closes back up
            if curr.l <= fib <= curr.h and curr.c > fib:
                entry = curr.c
                sl = lo - sl_buf
                tp = entry + (entry - sl) * rr
                out.append(Signal(id=f"{self.id}-{int(time())}", time=curr.t, symbol=symbol,
                                  strategy=self.id, side="BUY", entry=entry, sl=sl, tp=tp,
                                  note=f"Long retracement @{level}"))
        else:
            fib = lo + (hi - lo) * level
            if curr.l <= fib <= curr.h and curr.c < fib:
                entry = curr.c
                sl = hi + sl_buf
                tp = entry - (sl - entry) * rr
                out.append(Signal(id=f"{self.id}-{int(time())}", time=curr.t, symbol=symbol,
                                  strategy=self.id, side="SELL", entry=entry, sl=sl, tp=tp,
                                  note=f"Short retracement @{level}"))
        return out

def create(): return FibonacciRetracement()
