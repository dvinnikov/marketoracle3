import type { SignalResponse } from './api';

const WS_URL = import.meta.env.VITE_BACKEND_WS;

type MarketTopic = 'price.tick' | 'bar.update' | 'signal.new';

export type MarketMessage =
  | { topic: 'price.tick'; data: { symbol: string; bid: number; ask: number; time: number } }
  | { topic: 'bar.update'; data: { symbol: string; tf: number; bar: { t: number; o: number; h: number; l: number; c: number; v?: number | null } } }
  | { topic: 'signal.new'; data: SignalResponse };

export interface MarketStreamCallbacks {
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  onMessage?: (message: MarketMessage) => void;
}

export function connectMarketStream(callbacks: MarketStreamCallbacks) {
  const ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    callbacks.onOpen?.();
  };

  ws.onclose = () => {
    callbacks.onClose?.();
  };

  ws.onerror = (event) => {
    callbacks.onError?.(event);
  };

  ws.onmessage = (event) => {
    try {
      const parsed = JSON.parse(event.data) as { topic: MarketTopic; data: unknown };
      if (!parsed?.topic) return;
      callbacks.onMessage?.(parsed as MarketMessage);
    } catch (error) {
      console.error('Failed to parse market message', error);
    }
  };

  return () => {
    ws.close();
  };
}
