from __future__ import annotations
from time import time
from server.core.models import Signal, Bar, Timeframe

class Breakout:
    id = "breakout"
    name = "Breakout Strategy"
    description = "Break of recent range with optional retest."
    settingsSchema = {
        "range_lookback": {"type":"number","default":20,"min":5,"max":200},
        "confirm_retest": {"type":"boolean","default": True},
        "sl_buffer_mult": {"type":"number","default": 0.5},
        "tp_rr": {"type":"number","default": 1.5},  # R-multiple
        "lookback": {"type":"number","default": 200}
    }

    def on_init(self, ctx): self.ctx = ctx

    def on_bar(self, symbol: str, tf: Timeframe, bar: Bar):
        n  = int(self.ctx.get_setting("range_lookback", 20))
        retest = bool(self.ctx.get_setting("confirm_retest", True))
        sl_mult = float(self.ctx.get_setting("sl_buffer_mult", 0.5))
        rr = float(self.ctx.get_setting("tp_rr", 1.5))
        look = int(self.ctx.get_setting("lookback", 200))

        bars = self.ctx.get_bars(symbol, tf, look)
        if len(bars) < n + 3: return []
        prev = bars[-2]; curr = bars[-1]
        window = bars[-(n+1):-1]
        hi = max(b.h for b in window)
        lo = min(b.l for b in window)

        out = []
        # Up-break
        if prev.c <= hi and curr.c > hi:
            entry = curr.c
            sl = hi - (hi - lo) * sl_mult
            tp = entry + (entry - sl) * rr
            if not retest or curr.l <= hi <= curr.h:
                out.append(Signal(id=f"{self.id}-{int(time())}", time=curr.t, symbol=symbol,
                                  strategy=self.id, side="BUY", entry=entry, sl=sl, tp=tp,
                                  note=f"Range breakout ↑ {n}"))
        # Down-break
        if prev.c >= lo and curr.c < lo:
            entry = curr.c
            sl = lo + (hi - lo) * sl_mult
            tp = entry - (sl - entry) * rr
            if not retest or curr.l <= lo <= curr.h:
                out.append(Signal(id=f"{self.id}-{int(time())}", time=curr.t, symbol=symbol,
                                  strategy=self.id, side="SELL", entry=entry, sl=sl, tp=tp,
                                  note=f"Range breakout ↓ {n}"))
        return out

def create(): return Breakout()
