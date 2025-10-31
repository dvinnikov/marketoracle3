from __future__ import annotations
from time import time
from server.core.models import Signal, Bar, Timeframe
from server.core.indicators import rsi  # assuming your indicators module exposes rsi(closes, period)

class RSIDivergence:
    id = "rsi_divergence"
    name = "RSI Divergence"
    description = "Regular bullish/bearish divergence at swing zones."
    settingsSchema = {
        "period": {"type":"number","default":14,"min":5,"max":50},
        "pivot": {"type":"number","default":5},
        "rr": {"type":"number","default":1.8},
        "lookback": {"type":"number","default":200}
    }

    def on_init(self, ctx): self.ctx = ctx

    def _pivots(self, arr, lb):
        highs, lows = [], []
        for i in range(lb, len(arr)-lb):
            if all(arr[i] > arr[j] for j in range(i-lb, i)) and all(arr[i] > arr[j] for j in range(i+1, i+1+lb)):
                highs.append(i)
            if all(arr[i] < arr[j] for j in range(i-lb, i)) and all(arr[i] < arr[j] for j in range(i+1, i+1+lb)):
                lows.append(i)
        return highs, lows

    def on_bar(self, symbol: str, tf: Timeframe, bar: Bar):
        P = int(self.ctx.get_setting("period", 14))
        lb = int(self.ctx.get_setting("pivot", 5))
        rr = float(self.ctx.get_setting("rr", 1.8))
        look = int(self.ctx.get_setting("lookback", 200))

        bars = self.ctx.get_bars(symbol, tf, look)
        if len(bars) < P + lb + 5: return []
        closes = [b.c for b in bars]
        rs = rsi(closes, P)
        if len(rs) != len(closes): return []

        highs, lows = self._pivots(closes, lb)
        out = []
        # Bullish divergence: price lower low, RSI higher low
        if len(lows) >= 2:
            i1, i2 = lows[-2], lows[-1]
            if closes[i2] < closes[i1] and rs[i2] > rs[i1]:
                curr = bars[-1]; entry = curr.c; sl = bars[i2].l; tp = entry + (entry - sl) * rr
                out.append(Signal(id=f"{self.id}-{int(time())}", time=curr.t, symbol=symbol,
                                  strategy=self.id, side="BUY", entry=entry, sl=sl, tp=tp,
                                  note="Bullish RSI divergence"))
        # Bearish divergence: price higher high, RSI lower high
        if len(highs) >= 2:
            i1, i2 = highs[-2], highs[-1]
            if closes[i2] > closes[i1] and rs[i2] < rs[i1]:
                curr = bars[-1]; entry = curr.c; sl = bars[i2].h; tp = entry - (sl - entry) * rr
                out.append(Signal(id=f"{self.id}-{int(time())}", time=curr.t, symbol=symbol,
                                  strategy=self.id, side="SELL", entry=entry, sl=sl, tp=tp,
                                  note="Bearish RSI divergence"))
        return out

def create(): return RSIDivergence()
