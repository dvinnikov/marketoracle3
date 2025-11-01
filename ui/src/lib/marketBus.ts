// src/lib/marketBus.ts
export const BACKEND_WS = import.meta.env.VITE_BACKEND_WS ?? "ws://127.0.0.1:8000/ws/market";

export type WsPriceTick = {
  type: "price.tick";
  symbol: string;
  bid?: number;
  ask?: number;
  mid?: number;
  ts: number; // seconds
};

export type WsBarUpdate = {
  type: "bar.update";
  symbol: string;
  tf: number;   // timeframe seconds or minutes (backend contract)
  t: number;    // epoch seconds
  o: number; h: number; l: number; c: number; v?: number;
  is_final?: boolean;
};

export type WsSignalNew = {
  type: "signal.new";
  payload: {
    id: string;
    ts: number;
    symbol: string;
    strategy: string;
    side: "BUY" | "SELL";
    entry: number;
    stop: number;
    target: number;
  };
};

export type WsServerMessage = WsPriceTick | WsBarUpdate | WsSignalNew;

type Handler = (msg: WsServerMessage) => void;

export class MarketBus {
  private ws?: WebSocket;
  private handlers = new Set<Handler>();
  private reconnectTimer?: number;
  private wantsOpen = false;

  /** Connect and keep alive until `close()` is called. */
  open() {
    this.wantsOpen = true;
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) return;
    this.ws = new WebSocket(BACKEND_WS);

    this.ws.onopen = () => {
      // optional: send hello/ping
      // console.debug("[WS] open");
    };

    this.ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data) as WsServerMessage;
        this.handlers.forEach(h => h(msg));
      } catch (e) {
        console.warn("[WS] parse error", e);
      }
    };

    this.ws.onclose = () => {
      // console.warn("[WS] closed");
      this.scheduleReconnect();
    };

    this.ws.onerror = () => {
      // console.warn("[WS] error");
      this.ws?.close();
    };
  }

  private scheduleReconnect() {
    if (!this.wantsOpen) return;
    if (this.reconnectTimer) window.clearTimeout(this.reconnectTimer);
    this.reconnectTimer = window.setTimeout(() => this.open(), 1200);
  }

  close() {
    this.wantsOpen = false;
    if (this.reconnectTimer) window.clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = undefined;
  }

  subscribe(handler: Handler) {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }
}

/** Helper to filter messages for a given symbol/timeframe in your components */
export function filterBySymbolTf(
  handler: Handler,
  { symbol, tf }: { symbol: string; tf?: number }
): Handler {
  return (msg: WsServerMessage) => {
    if ("symbol" in msg && msg.symbol !== symbol) return;
    if (msg.type === "bar.update" && tf && msg.tf !== tf) return;
    handler(msg);
  };
}
