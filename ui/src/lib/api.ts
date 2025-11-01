// src/lib/api.ts
export const BACKEND_BASE = import.meta.env.VITE_BACKEND_BASE ?? "http://127.0.0.1:8000";

type HttpMethod = "GET" | "POST";
async function request<T>(path: string, method: HttpMethod = "GET", body?: any): Promise<T> {
  const res = await fetch(`${BACKEND_BASE}${path}`, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${method} ${path} -> ${res.status} ${res.statusText} ${text}`);
  }
  return res.json() as Promise<T>;
}

/** ---------- Types from backend ---------- */
export type Instrument = { symbol: string; name?: string };
export type Candle = { t: number; o: number; h: number; l: number; c: number; v?: number };
export type Strategy = { id: string; name: string; enabled?: boolean; description?: string };
export type Signal = {
  id: string;
  ts: number;
  symbol: string;
  strategy: string;
  side: "BUY" | "SELL";
  entry: number;
  stop: number;
  target: number;
  status?: "OPEN" | "CLOSED" | "CANCELLED" | "STOPPED";
  pnl?: number;
};
export type Prediction = {
  symbol: string;
  tf: number;
  direction: "BULLISH" | "BEARISH" | "NEUTRAL";
  confidence: number; // 0..100
  targetPrice?: number;
};

/** ---------- Endpoints ---------- */
export const api = {
  health: () => request<{ ok: boolean; time: string }>("/healthz"),

  listInstruments: () => request<Instrument[]>("/api/instruments"),

  candles: (symbol: string, timeframe = 60, limit = 300) =>
    request<Candle[]>(`/api/candles?symbol=${encodeURIComponent(symbol)}&timeframe=${timeframe}&limit=${limit}`),

  strategies: () => request<Strategy[]>("/api/strategies"),

  enableStrategy: (id: string, symbol: string, tf = 60, settings: Record<string, any> = {}) =>
    request<{ ok: boolean }>(`/api/strategies/enable`, "POST", { id, symbol, tf, settings }),

  disableStrategy: (id: string, symbol: string, tf = 60) =>
    request<{ ok: boolean }>(`/api/strategies/disable`, "POST", { id, symbol, tf }),

  signals: (symbol: string) =>
    request<Signal[]>(`/api/signals?symbol=${encodeURIComponent(symbol)}`),

  prediction: (symbol: string, tf = 60) =>
    request<Prediction>(`/api/prediction?symbol=${encodeURIComponent(symbol)}&tf=${tf}`),
};

/** ---------- UI-friendly mappers ---------- */
export function toKline(source: Candle[]) {
  // Map server candle -> your chart’s expected shape if needed
  return source.map(c => ({
    timestamp: c.t * 1000,
    open: c.o,
    high: c.h,
    low: c.l,
    close: c.c,
    volume: c.v ?? 0,
  }));
}
