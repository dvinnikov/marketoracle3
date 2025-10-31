from __future__ import annotations
from time import time
from server.core.models import Signal, Bar, Timeframe

class SupportResistance:
    id = "support_resistance"
    name = "Support/Resistance"
    description = "Trades bounces off detected swing levels."
    settingsSchema = {
        "pivot_lookback": {"type":"number","default":5,"min":2,"max":20},
        "touch_tolerance_pips": {"type":"number","default":5},
        "sl_buffer_pips": {"type":"number","default":6},
        "tp_buffer_pips": {"type":"number","default":10},
        "scan_bars": {"type":"number","default":200}
    }

    def on_init(self, ctx): self.ctx = ctx

    def _pips(self, symbol, p):
        point = self.ctx.get_symbol_point(symbol) or 0.0001
        return p * point * 10  # pip ≈ 10 * point for most FX (5-digit)

    def _swings(self, bars, lb):
        # Very simple pivot highs/lows
        S, R = [], []
        for i in range(lb, len(bars)-lb):
            left  = bars[i-lb:i]
            right = bars[i+1:i+1+lb]
            high = max(b.h for b in left+right)
            low  = min(b.l for b in left+right)
            if bars[i].h > high: R.append(bars[i].h)
            if bars[i].l < low:  S.append(bars[i].l)
        # keep last few recent levels
        return S[-8:], R[-8:]

    def on_bar(self, symbol: str, tf: Timeframe, bar: Bar):
        lb = int(self.ctx.get_setting("pivot_lookback", 5))
        scan = int(self.ctx.get_setting("scan_bars", 200))
        tol = self._pips(symbol, float(self.ctx.get_setting("touch_tolerance_pips", 5)))
        slp = self._pips(symbol, float(self.ctx.get_setting("sl_buffer_pips", 6)))
        tpp = self._pips(symbol, float(self.ctx.get_setting("tp_buffer_pips", 10)))

        bars = self.ctx.get_bars(symbol, tf, scan)
        if len(bars) < lb*2+5: return []

        S, R = self._swings(bars, lb)
        if not S and not R: return []
        curr = bars[-1]

        out = []
        # bounce buy: low near support and close above it
        for s in reversed(S):
            if abs(curr.l - s) <= tol and curr.c > s:
                out.append(Signal(
                    id=f"{self.id}-{int(time())}", time=curr.t, symbol=symbol,
                    strategy=self.id, side="BUY", entry=curr.c,
                    sl=s - slp, tp=curr.c + (tpp),
                    note="Bounce from support"
                ))
                break
        # rejection sell: high near resistance and close below it
        for r in reversed(R):
            if abs(curr.h - r) <= tol and curr.c < r:
                out.append(Signal(
                    id=f"{self.id}-{int(time())}", time=curr.t, symbol=symbol,
                    strategy=self.id, side="SELL", entry=curr.c,
                    sl=r + slp, tp=curr.c - (tpp),
                    note="Rejection from resistance"
                ))
                break
        return out

def create(): return SupportResistance()
