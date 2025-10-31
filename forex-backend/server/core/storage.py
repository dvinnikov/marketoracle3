from __future__ import annotations
from typing import List, Optional
from .models import Signal

_LOG: List[Signal] = []

def add_signal(sig: Signal) -> None:
    _LOG.insert(0, sig)

def list_signals(symbol: Optional[str] = None, limit: int = 200) -> list[Signal]:
    if symbol:
        return [s for s in _LOG if s.symbol == symbol][:limit]
    return _LOG[:limit]
