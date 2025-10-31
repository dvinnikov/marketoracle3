from __future__ import annotations
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple, List, Optional
from .models import Bar, Tick, Timeframe, Account, Position, Order

class MarketState:
    def __init__(self, max_bars: int = 2000) -> None:
        self.ticks: Dict[str, Tick] = {}
        self.bars: Dict[tuple[str, Timeframe], Deque[Bar]] = defaultdict(lambda: deque(maxlen=max_bars))
        self.instruments: List[dict] = []
        self.account: Optional[Account] = None
        self.positions: List[Position] = []
        self.orders: List[Order] = []
        self.status: str = "running"

STATE = MarketState()
