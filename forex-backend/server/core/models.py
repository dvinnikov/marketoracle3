from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Literal

Timeframe = int  # minutes

@dataclass
class Tick:
    symbol: str
    bid: float
    ask: float
    time: int  # epoch seconds

@dataclass
class Bar:
    t: int
    o: float
    h: float
    l: float
    c: float
    v: float | None = None

@dataclass
class Account:
    login: int
    name: str
    server: str
    currency: str
    balance: float
    equity: float
    margin: float

@dataclass
class Position:
    ticket: int
    symbol: str
    type: int
    volume: float
    price: float
    sl: float
    tp: float
    profit: float
    time: int

@dataclass
class Order:
    ticket: int
    symbol: str
    type: int
    volume: float
    price: float
    sl: float
    tp: float
    time: int

@dataclass
class Signal:
    id: str
    time: int
    symbol: str
    strategy: str
    side: Literal["BUY","SELL"]
    entry: float
    sl: float | None = None
    tp: float | None = None
    result: Optional[Literal["WIN","LOSS","BE","OPEN"]] = "OPEN"
    pnl: float | None = None

@dataclass
class Prediction:
    symbol: str
    tf: Timeframe
    target: float | None
    confidence: float | None
