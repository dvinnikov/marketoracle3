from __future__ import annotations
from time import time
from statistics import mean, pstdev
from server.core.models import Signal, Bar, Timeframe

class BollingerBounce:
    id = "bollinger_bounce"
    name = "Bollinger Bounce"
    description = "Mean reversion using Bollinger Band touches & re-entry."
    settingsSchema = {
        "period": {"type": "number", "default": 20, "min": 5, "max": 200},
        "mult":   {"type": "number", "default": 2.0, "step": 0.1},
        "confirm": {"type": "boolean", "default": True},  # require close back inside bands
        "sl_mult": {"type": "number", "default": 0.5},
        "tp_mult": {"type": "number", "default": 1.0},
        "lookback": {"type": "number", "default": 120},
    }

    def on_init(self, ctx): self.ctx = ctx

    def _bands(self, closes, period, mult):
        if len(closes) < period: return None
        window = closes[-period:]
        m = mean(window)
        sd = pstdev(window) if period > 1 else 0.0
        return (m, m + mult * sd, m - mult * sd)

    def on_bar(self, symbol: str, tf: Timeframe, bar: Bar):
        P  = int(self.ctx.get_setting("period", 20))
        K  = float(self.ctx.get_setting("mult", 2.0))
        confirm = bool(self.ctx.get_setting("confirm", True))
        lookback = int(self.ctx.get_setting("lookback", 120))
        sl_mult = float(self.ctx.get_setting("sl_mult", 0.5))
        tp_mult = float(self.ctx.get_setting("tp_mult", 1.0))

        bars = self.ctx.get_bars(symbol, tf, lookback)
        if len(bars) < max(30, P+2): return []

        closes = [b.c for b in bars]
        res = self._bands(closes, P, K)
        if not res: return []
        mid, upper, lower = res

        prev = bars[-2]
        curr = bars[-1]

        signals = []
        # Touch lower band then close back above (mean reversion BUY)
        if prev.l <= lower and (not confirm or curr.c > lower):
            entry = curr.c
            sl = entry - (mid - lower) * sl_mult
            tp = entry + (mid - lower) * tp_mult
            signals.append(Signal(
                id=f"{self.id}-{int(time())}",
                time=curr.t, symbol=symbol, strategy=self.id,
                side="BUY", entry=entry, sl=sl, tp=tp,
                note=f"Bounce from lower band (P={P},K={K})"
            ))
        # Touch upper band then close back below (mean reversion SELL)
        if prev.h >= upper and (not confirm or curr.c < upper):
            entry = curr.c
            sl = entry + (upper - mid) * sl_mult
            tp = entry - (upper - mid) * tp_mult
            signals.append(Signal(
                id=f"{self.id}-{int(time())}",
                time=curr.t, symbol=symbol, strategy=self.id,
                side="SELL", entry=entry, sl=sl, tp=tp,
                note=f"Rejection from upper band (P={P},K={K})"
            ))
        return signals

def create(): return BollingerBounce()
