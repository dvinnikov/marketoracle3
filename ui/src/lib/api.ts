const BASE_URL = import.meta.env.VITE_BACKEND_BASE;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const response = await fetch(url, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Request failed: ${response.status} ${response.statusText}${text ? ` - ${text}` : ''}`);
  }

  return response.json() as Promise<T>;
}

export interface Instrument {
  symbol: string;
  name?: string;
  description?: string;
  digits?: number;
  point?: number;
}

export async function fetchInstruments(signal?: AbortSignal): Promise<Instrument[]> {
  const data = await request<{ symbols: Instrument[] }>(`/api/instruments`, { signal });
  return data.symbols ?? [];
}

export interface CandleResponse {
  bars: Array<{
    t: number;
    o: number;
    h: number;
    l: number;
    c: number;
    v?: number | null;
  }>;
}

export interface CandlePoint {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export async function fetchCandles(params: { symbol: string; timeframe: number; limit: number }, signal?: AbortSignal): Promise<CandlePoint[]> {
  const query = new URLSearchParams({
    symbol: params.symbol,
    timeframe: String(params.timeframe),
    limit: String(params.limit),
  });
  const data = await request<CandleResponse>(`/api/candles?${query.toString()}`, { signal });
  return (data.bars ?? []).map((bar) => ({
    timestamp: bar.t * 1000,
    open: bar.o,
    high: bar.h,
    low: bar.l,
    close: bar.c,
    volume: bar.v ?? 0,
  }));
}

export interface Strategy {
  id: string;
  name: string;
  description?: string;
  settingsSchema?: Record<string, unknown>;
  enabled?: boolean;
  winRate?: number;
}

export async function fetchStrategies(signal?: AbortSignal): Promise<Strategy[]> {
  const data = await request<Strategy[]>(`/api/strategies`, { signal });
  return data.map((strategy) => ({
    ...strategy,
    enabled: Boolean(strategy.enabled),
  }));
}

interface StrategyPayload {
  id: string;
  symbol: string;
  tf: number;
  settings?: Record<string, unknown>;
}

export async function enableStrategy(payload: StrategyPayload): Promise<void> {
  await request(`/api/strategies/enable`, {
    method: 'POST',
    body: JSON.stringify({ ...payload, settings: payload.settings ?? {} }),
  });
}

export async function disableStrategy(payload: StrategyPayload): Promise<void> {
  await request(`/api/strategies/disable`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export interface SignalResponse {
  id: string;
  time: number;
  symbol: string;
  strategy: string;
  side: 'BUY' | 'SELL';
  entry: number;
  sl?: number | null;
  tp?: number | null;
  result?: 'WIN' | 'LOSS' | 'BE' | 'OPEN';
  pnl?: number | null;
}

export async function fetchSignals(params: { symbol: string }, signal?: AbortSignal): Promise<SignalResponse[]> {
  const query = new URLSearchParams({ symbol: params.symbol });
  const data = await request<{ items: SignalResponse[] }>(`/api/signals?${query.toString()}`, { signal });
  return data.items ?? [];
}

export interface PredictionResponse {
  symbol: string;
  tf: number;
  target: number | null;
  confidence: number | null;
}

export async function fetchPrediction(params: { symbol: string; timeframe: number }, signal?: AbortSignal): Promise<PredictionResponse> {
  const query = new URLSearchParams({ symbol: params.symbol, tf: String(params.timeframe) });
  return request<PredictionResponse>(`/api/prediction?${query.toString()}`, { signal });
}

export function formatInstrumentLabel(instrument: Instrument): { label: string; name: string } {
  const symbol = instrument.symbol;
  const label = symbol.length > 3 ? `${symbol.slice(0, 3)}/${symbol.slice(3)}` : symbol;
  const name = instrument.name ?? symbol;
  return { label, name };
}
