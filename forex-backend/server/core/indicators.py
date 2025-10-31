from __future__ import annotations

def sma(values: list[float], n: int) -> float:
    if not values or n <= 0 or len(values) < n:
        return float("nan")
    return sum(values[-n:]) / n

def ema(values: list[float], n: int) -> float:
    if not values or n <= 0:
        return float("nan")
    k = 2 / (n + 1)
    e = values[0]
    for v in values[1:]:
        e = v * k + e * (1 - k)
    return e

def rsi(closes: list[float], period: int = 14) -> float:
    if len(closes) < period + 1: return float("nan")
    gains = []
    losses = []
    for i in range(1, period + 1):
        ch = closes[-i] - closes[-i-1]
        gains.append(max(0.0, ch))
        losses.append(max(0.0, -ch))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0: return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))
