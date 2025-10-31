from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple
import asyncio, time
from .models import Bar, Signal, Timeframe
from .state import STATE
from .ws import WS_HUB
from .storage import add_signal

@dataclass
class ActiveStrategy:
    inst: any
    settings: dict

class StrategyOrchestrator:
    def __init__(self) -> None:
        self.active: Dict[Tuple[str,str,Timeframe], ActiveStrategy] = {}

    def enable(self, id: str, inst: any, symbol: str, tf: Timeframe, settings: dict) -> None:
        self.active[(symbol, id, tf)] = ActiveStrategy(inst=inst, settings=settings)
        if hasattr(inst, "on_init"):
            inst.on_init(self._ctx(symbol, tf, settings))

    def disable(self, id: str, symbol: str, tf: Timeframe) -> None:
        self.active.pop((symbol, id, tf), None)

    def on_bar(self, symbol: str, tf: Timeframe, bar: Bar) -> None:
        for (sym, id, tf0), a in list(self.active.items()):
            if sym != symbol or tf0 != tf: continue
            if hasattr(a.inst, "on_bar"):
                signals = a.inst.on_bar(symbol, tf, bar) or []
                for s in signals:
                    add_signal(s)
                    asyncio.create_task(WS_HUB.broadcast("signal.new", s.__dict__))

    def _ctx(self, symbol: str, tf: Timeframe, settings: dict):
        class Ctx:
            def get_bars(self, sym, tfv, lookback):
                dq = STATE.bars.get((sym, tfv))
                if not dq: return []
                return list(dq)[-lookback:]
            def get_setting(self, key, default=None):
                return settings.get(key, default)
        return Ctx()

ORCH = StrategyOrchestrator()
