from __future__ import annotations
from typing import Callable, Iterable
from .models import Tick, Bar, Timeframe
from .state import STATE

class BarAggregator:
    def __init__(self, on_bar_close: Callable[[str, Timeframe, Bar], None]) -> None:
        self.on_bar_close = on_bar_close

    def ingest_tick(self, symbol: str, tick: Tick, tfs: Iterable[Timeframe]) -> list[tuple[str, Timeframe, Bar]]:
        updates: list[tuple[str, Timeframe, Bar]] = []
        for tf in tfs:
            bucket = (tick.time // (tf * 60)) * (tf * 60)
            dq = STATE.bars[(symbol, tf)]
            if dq and dq[-1].t == bucket:
                b = dq[-1]
                b.h = max(b.h, tick.ask)
                b.l = min(b.l, tick.bid)
                b.c = (tick.bid + tick.ask) / 2
                updates.append((symbol, tf, b))
            else:
                # close previous
                if dq and dq[-1].t < bucket:
                    self.on_bar_close(symbol, tf, dq[-1])
                # open new bar
                mid = (tick.bid + tick.ask) / 2
                b = Bar(t=bucket, o=mid, h=mid, l=mid, c=mid)
                dq.append(b)
                updates.append((symbol, tf, b))
        return updates
