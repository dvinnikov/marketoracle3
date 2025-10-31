#!/usr/bin/env python3
"""
Scaffold a React+Vite frontend and FastAPI backend for a Forex platform.

Usage:
  python scaffold_forex_platform.py --dest ./forex-platform [--overwrite]

This script creates the exact folder/file structure and contents.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

FILES: dict[str, str] = {}

def add(path: str, body: str) -> None:
    FILES[path.replace("\\", "/")] = body

def write_all(dest: Path, overwrite: bool) -> None:
    for rel, body in FILES.items():
        full = dest / rel
        full.parent.mkdir(parents=True, exist_ok=True)
        if full.exists() and not overwrite:
            print(f"[skip] {full} (exists, use --overwrite to replace)")
            continue
        full.write_text(body, encoding="utf-8", newline="\n")
        print(f"[write] {full}")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default="forex-platform", help="Destination directory (will be created if missing)")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    args = ap.parse_args()

    dest = Path(args.dest).resolve()
    dest.mkdir(parents=True, exist_ok=True)
    print(f"Scaffolding into: {dest}")

    # ----- FRONTEND -----
    add("frontend/package.json", """{
  "name": "forex-frontend",
  "private": true,
  "version": "0.0.1",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "server": "node server.js"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.2",
    "@types/react-dom": "^18.3.0",
    "typescript": "^5.6.2",
    "vite": "^5.4.0",
    "@vitejs/plugin-react": "^4.3.1"
  }
}""")

    add("frontend/tsconfig.json", """{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "jsx": "react-jsx",
    "moduleResolution": "Bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "strict": true
  },
  "include": ["src"]
}""")

    add("frontend/vite.config.ts", """import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/udf": "http://127.0.0.1:8000",
      "/ws": {
        target: "ws://127.0.0.1:8000",
        ws: true
      }
    }
  }
});""")

    add("frontend/.env.example", "VITE_API_BASE=http://127.0.0.1:8000\n")

    add("frontend/index.html", """<!doctype html>
<html>
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>Forex UI</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
""")

    add("frontend/src/main.tsx", """import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode><App/></React.StrictMode>
);
""")

    add("frontend/src/App.tsx", """import React, { useEffect, useState } from "react";
import { InstrumentSelector } from "./features/strategies/InstrumentSelector";
import { StrategyList } from "./features/strategies/StrategyList";
import { PredictionCard } from "./features/prediction/PredictionCard";
import { SignalLog } from "./features/log/SignalLog";
import { TVChart } from "./features/chart/TVChart";
import { apiBase } from "./lib/env";
import { wsConnect } from "./lib/marketBus";

export default function App() {
  const [symbol, setSymbol] = useState("EURUSD");
  const [tf, setTf] = useState(60);

  useEffect(() => {
    const ws = wsConnect();
    return () => ws.close();
  }, []);

  return (
    <div className="wrap">
      <header>
        <h1>Forex Platform</h1>
        <div className="row">
          <InstrumentSelector symbol={symbol} onChange={setSymbol} />
          <select value={tf} onChange={e => setTf(parseInt(e.target.value))}>
            <option value={1}>M1</option><option value={5}>M5</option>
            <option value={15}>M15</option><option value={60}>H1</option>
          </select>
        </div>
      </header>
      <main className="grid">
        <section className="chart">
          <TVChart symbol={symbol} timeframe={tf} />
        </section>
        <aside className="side">
          <StrategyList symbol={symbol} timeframe={tf} />
          <PredictionCard symbol={symbol} timeframe={tf} />
          <SignalLog symbol={symbol} />
        </aside>
      </main>
      <footer>API: {apiBase}</footer>
    </div>
  );
}
""")

    add("frontend/src/styles.css", """body { margin:0; font-family: system-ui, sans-serif; color:#eee; background:#0f1115; }
.wrap { display:flex; flex-direction:column; min-height:100vh; }
header { padding:12px 16px; background:#161a22; border-bottom:1px solid #282c34; }
.row { display:flex; gap:8px; align-items:center; }
.grid { display:grid; grid-template-columns: 1fr 360px; gap:12px; padding:12px; }
.chart { background:#11151d; border:1px solid #252a34; border-radius:10px; min-height:520px; }
.side { display:flex; flex-direction:column; gap:12px; }
section, aside > * { background:#11151d; border:1px solid #252a34; border-radius:10px; padding:10px; }
select { background:#0f1115; color:#eee; border:1px solid #3a3f4b; border-radius:6px; padding:6px; }
""")

    add("frontend/src/vite-env.d.ts", "/// <reference types=\"vite/client\" />\n")

    add("frontend/src/lib/env.ts", """export const apiBase = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";""")

    add("frontend/src/lib/api.ts", """import { apiBase } from "./env";
export async function getJSON<T>(url: string): Promise<T> {
  const r = await fetch(apiBase + url);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}
export async function postJSON<T>(url: string, body: any): Promise<T> {
  const r = await fetch(apiBase + url, {
    method: "POST",
    headers: { "Content-Type":"application/json" },
    body: JSON.stringify(body)
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}
""")

    add("frontend/src/lib/marketBus.ts", """import { apiBase } from "./env";

export function wsConnect(): WebSocket {
  const url = apiBase.replace(/^http/, "ws") + "/ws/market";
  const ws = new WebSocket(url);
  ws.onopen = () => console.log("[WS] open");
  ws.onclose = () => console.log("[WS] close");
  ws.onerror = (e) => console.warn("[WS] error", e);
  ws.onmessage = (e) => {
    try { const msg = JSON.parse(e.data); window.dispatchEvent(new CustomEvent(msg.topic, { detail: msg.data })); }
    catch (err) { console.warn("WS parse", err); }
  };
  return ws;
}
""")

    add("frontend/src/lib/useMarketData.ts", """import { useEffect, useState } from "react";
export function useWsTopic<T>(topic: string, initial: T) {
  const [data, setData] = useState<T>(initial);
  useEffect(() => {
    const handler = (e: any) => setData(e.detail);
    window.addEventListener(topic, handler as EventListener);
    return () => window.removeEventListener(topic, handler as EventListener);
  }, [topic]);
  return data;
}
""")

    add("frontend/src/features/chart/TVChart.tsx", """import React, { useEffect, useState } from "react";
import { getJSON } from "../../lib/api";
import { useWsTopic } from "../../lib/useMarketData";

type Bar = { t:number; o:number; h:number; l:number; c:number; v?:number };

export function TVChart({ symbol, timeframe }:{symbol:string; timeframe:number}) {
  const [bars, setBars] = useState<Bar[]>([]);
  const liveBar = useWsTopic<any>("bar.update", null);

  useEffect(() => {
    getJSON<{bars:Bar[]}>(`/api/candles?symbol=${symbol}&timeframe=${timeframe}&limit=300`)
      .then(x => setBars(x.bars)).catch(console.error);
  }, [symbol, timeframe]);

  useEffect(() => {
    if (!liveBar) return;
    if (liveBar.symbol !== symbol || liveBar.tf !== timeframe) return;
    setBars(prev => {
      const next = [...prev];
      const last = next[next.length-1];
      if (last && last.t === liveBar.bar.t) next[next.length-1] = liveBar.bar;
      else next.push(liveBar.bar);
      return next.slice(-500);
    });
  }, [liveBar, symbol, timeframe]);

  return (
    <div>
      <div style={{opacity:.7, marginBottom:8}}>{symbol} / TF {timeframe}</div>
      <pre style={{maxHeight:460, overflow:"auto"}}>{JSON.stringify(bars.slice(-5), null, 2)}</pre>
    </div>
  );
}
""")

    add("frontend/src/features/strategies/InstrumentSelector.tsx", """import React, { useEffect, useState } from "react";
import { getJSON } from "../../lib/api";

export function InstrumentSelector({symbol, onChange}:{symbol:string; onChange:(s:string)=>void}) {
  const [list, setList] = useState<{symbol:string}[]>([]);
  useEffect(() => { getJSON<{symbols:{symbol:string}[]}>("/api/instruments").then(x => setList(x.symbols)); }, []);
  return (
    <select value={symbol} onChange={e=>onChange(e.target.value)}>
      {list.map(x => <option key={x.symbol} value={x.symbol}>{x.symbol}</option>)}
    </select>
  );
}
""")

    add("frontend/src/features/strategies/StrategyList.tsx", """import React, { useEffect, useState } from "react";
import { getJSON, postJSON } from "../../lib/api";

export function StrategyList({symbol, timeframe}:{symbol:string; timeframe:number}) {
  const [catalog, setCatalog] = useState<any[]>([]);
  const refresh = () => getJSON<any[]>("/api/strategies").then(setCatalog);
  useEffect(() => { refresh(); }, []);

  const enable = async (id:string) => {
    await postJSON("/api/strategies/enable", { id, symbol, tf: timeframe, settings: {} });
    alert(`Enabled ${id} on ${symbol}/${timeframe}`);
  };
  const disable = async (id:string) => {
    await postJSON("/api/strategies/disable", { id, symbol, tf: timeframe });
    alert(`Disabled ${id}`);
  };

  return (
    <div>
      <h3>Strategies</h3>
      <ul>
        {catalog.map(s => (
          <li key={s.id} style={{display:"flex", gap:8, alignItems:"center"}}>
            <b>{s.name}</b><small style={{opacity:.7}}>{s.id}</small>
            <button onClick={()=>enable(s.id)}>Enable</button>
            <button onClick={()=>disable(s.id)}>Disable</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
""")

    add("frontend/src/features/prediction/PredictionCard.tsx", """import React from "react";
import { useWsTopic } from "../../lib/useMarketData";

export function PredictionCard({symbol, timeframe}:{symbol:string; timeframe:number}) {
  const pred = useWsTopic<any>("prediction.update", {symbol, timeframe, target:null, confidence:null});
  if (pred.symbol !== symbol || pred.tf !== timeframe) return <div><h3>Prediction</h3><div>Loading…</div></div>;
  return (
    <div>
      <h3>Prediction</h3>
      <div>Target: {pred.target ?? "-"}</div>
      <div>Confidence: {pred.confidence ?? "-"}</div>
    </div>
  );
}
""")

    add("frontend/src/features/log/SignalLog.tsx", """import React, { useEffect, useState } from "react";
import { getJSON } from "../../lib/api";
import { useWsTopic } from "../../lib/useMarketData";

export function SignalLog({symbol}:{symbol:string}) {
  const [rows, setRows] = useState<any[]>([]);
  const live = useWsTopic<any>("signal.new", null);

  useEffect(() => {
    getJSON<any>(`/api/signals?symbol=${symbol}`).then(x => setRows(x.items || []));
  }, [symbol]);

  useEffect(() => {
    if (!live || live.symbol !== symbol) return;
    setRows(prev => [live, ...prev].slice(0, 200));
  }, [live, symbol]);

  return (
    <div>
      <h3>Signal Logs</h3>
      <ul style={{maxHeight:220, overflow:"auto"}}>
        {rows.map((r,i) => <li key={r.id ?? i}>
          [{r.time}] {r.strategy} {r.side} @ {r.entry} → {r.result ?? "PENDING"} {r.pnl ? `(${r.pnl})` : ""}
        </li>)}
      </ul>
    </div>
  );
}
""")

    # ----- BACKEND -----
    add("server/pyproject.toml", """[project]
name = "forex-server"
version = "0.0.1"
requires-python = ">=3.10"
dependencies = [
  "fastapi>=0.115",
  "uvicorn[standard]>=0.30",
  "pydantic>=2.9",
  "pydantic-settings>=2.5"
]

[tool.uvicorn]
factory = true
host = "127.0.0.1"
port = 8000
reload = true
""")

    add("server/server/__init__.py", "")
    add("server/server/api/__init__.py", "")
    add("server/server/core/__init__.py", "")
    add("server/server/strategies/__init__.py", "")

    add("server/server/config.py", """from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    CORS_ORIGINS: list[str] = [\"http://127.0.0.1:5173\", \"http://localhost:5173\"]
    STRATEGIES_DIR: str = \"server/strategies\"

settings = Settings()
""")

    add("server/server/core/models.py", """from __future__ import annotations
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
    t: int; o: float; h: float; l: float; c: float; v: float | None = None

@dataclass
class Signal:
    id: str
    time: str
    symbol: str
    strategy: str
    side: Literal[\"BUY\",\"SELL\"]
    entry: float
    sl: float | None = None
    tp: float | None = None
    result: Optional[Literal[\"WIN\",\"LOSS\",\"BE\",\"OPEN\"]] = \"OPEN\"
    pnl: float | None = None

@dataclass
class Prediction:
    symbol: str
    tf: Timeframe
    target: float | None
    confidence: float | None
""")

    add("server/server/core/state.py", """from __future__ import annotations
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple
from .models import Bar, Tick, Timeframe

class MarketState:
    def __init__(self) -> None:
        self.ticks: Dict[str, Tick] = {}
        self.bars: Dict[Tuple[str, Timeframe], Deque[Bar]] = defaultdict(lambda: deque(maxlen=1200))
        self.instruments: list[dict] = []

STATE = MarketState()
""")

    add("server/server/core/bars.py", """from __future__ import annotations
from typing import Callable
from .models import Tick, Bar, Timeframe
from .state import STATE

class BarAggregator:
    def __init__(self, on_bar_close: Callable[[str, Timeframe, Bar], None]) -> None:
        self.on_bar_close = on_bar_close

    def ingest_tick(self, symbol: str, tick: Tick, tf: Timeframe = 60) -> None:
        # derive bucket start
        bucket = (tick.time // (tf * 60)) * (tf * 60)
        dq = STATE.bars[(symbol, tf)]
        if dq and dq[-1].t == bucket:
            b = dq[-1]
            b.h = max(b.h, tick.ask)
            b.l = min(b.l, tick.bid)
            b.c = (tick.bid + tick.ask) / 2
        else:
            if dq and dq[-1].t < bucket:
                self.on_bar_close(symbol, tf, dq[-1])
            mid = (tick.bid + tick.ask) / 2
            dq.append(Bar(t=bucket, o=mid, h=mid, l=mid, c=mid))
""")

    add("server/server/core/ws.py", """from __future__ import annotations
from typing import Any, Set
from fastapi import WebSocket

class WebSocketHub:
    def __init__(self) -> None:
        self.clients: Set[WebSocket] = set()

    async def register(self, ws: WebSocket) -> None:
        await ws.accept()
        self.clients.add(ws)

    def unregister(self, ws: WebSocket) -> None:
        self.clients.discard(ws)

    async def broadcast(self, topic: str, data: Any) -> None:
        dead = []
        for ws in list(self.clients):
            try:
                await ws.send_json({\"topic\": topic, \"data\": data})
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.unregister(ws)

WS_HUB = WebSocketHub()
""")

    add("server/server/core/loader.py", """from __future__ import annotations
import importlib.util, pathlib, types
from typing import Any

class StrategyMeta(dict): pass

class StrategyLoader:
    def __init__(self, base_dir: str) -> None:
        self.base_dir = pathlib.Path(base_dir)
        self.catalog: list[StrategyMeta] = []

    def discover(self) -> list[StrategyMeta]:
        self.catalog.clear()
        for p in sorted(self.base_dir.glob(\"*.py\")):
            if p.name == \"__init__.py\": continue
            mod = self._import_module(p)
            if hasattr(mod, \"create\"):
                inst = mod.create()
                self.catalog.append({
                    \"id\": getattr(inst, \"id\", p.stem),
                    \"name\": getattr(inst, \"name\", p.stem.replace(\"_\",\" \").title()),
                    \"description\": getattr(inst, \"description\", \"\"),
                    \"settingsSchema\": getattr(inst, \"settingsSchema\", {})
                })
        return self.catalog

    def load(self, id_or_name: str):
        for p in self.base_dir.glob(\"*.py\"):
            if p.stem == id_or_name:
                mod = self._import_module(p)
                return mod.create()
        raise KeyError(f\"strategy not found: {id_or_name}\")

    def _import_module(self, path: pathlib.Path) -> types.ModuleType:
        spec = importlib.util.spec_from_file_location(path.stem, path)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
""")

    add("server/server/core/orchestrator.py", """from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple
import asyncio
from .models import Bar, Timeframe
from .ws import WS_HUB

@dataclass
class ActiveStrategy:
    inst: any
    settings: dict

class StrategyOrchestrator:
    def __init__(self) -> None:
        self.active: Dict[Tuple[str,str,Timeframe], ActiveStrategy] = {}

    def enable(self, id: str, inst: any, symbol: str, tf: Timeframe, settings: dict) -> None:
        self.active[(symbol, id, tf)] = ActiveStrategy(inst=inst, settings=settings)
        if hasattr(inst, \"on_init\"):
            inst.on_init(self._ctx(symbol, tf, settings))

    def disable(self, id: str, symbol: str, tf: Timeframe) -> None:
        self.active.pop((symbol, id, tf), None)

    def on_bar(self, symbol: str, tf: Timeframe, bar: Bar) -> None:
        for (sym, id, tf0), a in list(self.active.items()):
            if sym != symbol or tf0 != tf: continue
            if hasattr(a.inst, \"on_bar\"):
                signals = a.inst.on_bar(symbol, tf, bar) or []
                for s in signals:
                    asyncio.create_task(WS_HUB.broadcast(\"signal.new\", s.__dict__))

    def _ctx(self, symbol: str, tf: Timeframe, settings: dict):
        from .state import STATE
        class Ctx:
            def get_bars(self, sym, tfv, lookback):
                dq = STATE.bars.get((sym, tfv))
                if not dq: return []
                return list(dq)[-lookback:]
            def get_setting(self, key, default=None):
                return settings.get(key, default)
        return Ctx()

ORCH = StrategyOrchestrator()
""")

    add("server/server/core/prediction.py", """from __future__ import annotations
from .state import STATE
from .models import Prediction, Timeframe

def predict(symbol: str, tf: Timeframe) -> Prediction:
    dq = STATE.bars.get((symbol, tf))
    if not dq or len(dq) < 2:
        return Prediction(symbol=symbol, tf=tf, target=None, confidence=None)
    last = dq[-1]
    prev = dq[-2]
    slope = last.c - prev.c
    target = last.c + slope * 3
    conf = min(0.95, max(0.05, abs(slope) * 100))
    return Prediction(symbol=symbol, tf=tf, target=round(target, 5), confidence=round(conf, 2))
""")

    add("server/server/core/storage.py", """from __future__ import annotations
from typing import List
from .models import Signal

LOG: List[Signal] = []

def add_signal(s: Signal) -> None:
    LOG.insert(0, s)

def list_signals(symbol: str | None = None, limit: int = 200):
    if symbol:
        return [x for x in LOG if x.symbol == symbol][:limit]
    return LOG[:limit]
""")

    add("server/server/api/bridge.py", """from __future__ import annotations
from fastapi import APIRouter, Body
from ..core.models import Tick
from ..core.state import STATE
from ..core.bars import BarAggregator
from ..core.orchestrator import ORCH
from ..core.ws import WS_HUB

router = APIRouter(prefix=\"/bridge\", tags=[\"bridge\"])
_agg = BarAggregator(lambda s,tf,b: ORCH.on_bar(s,tf,b))

@router.post(\"/tick\")
async def tick(payload: dict = Body(...)):
    t = Tick(symbol=payload[\"symbol\"], bid=float(payload[\"bid\"]), ask=float(payload[\"ask\"]), time=int(payload[\"time\"]))
    STATE.ticks[t.symbol] = t
    await WS_HUB.broadcast(\"price.tick\", t.__dict__)
    for tf in (1,5,15,60):
        _agg.ingest_tick(t.symbol, t, tf=tf)
    # also push a synthetic bar.update for current bucket (optional)
    # Not implemented: emit on every partial; typically emit only on close.
    return {\"ok\": True}

@router.post(\"/instruments\")
async def instruments(payload: dict = Body(...)):
    STATE.instruments = payload.get(\"symbols\", [])
    return {\"ok\": True}
""")

    add("server/server/api/rest.py", """from __future__ import annotations
from fastapi import APIRouter, Query
from ..core.state import STATE
from ..core.loader import StrategyLoader
from ..core.orchestrator import ORCH
from ..core.prediction import predict
from ..core.ws import WS_HUB
from ..config import settings

router = APIRouter()

_loader = StrategyLoader(settings.STRATEGIES_DIR)
_loader.discover()

@router.get(\"/healthz\")
def healthz():
    return {\"ok\": True, \"ticks\": len(STATE.ticks), \"symbols\": len(STATE.instruments)}

@router.get(\"/api/instruments\")
def api_instruments():
    return {\"symbols\": STATE.instruments or [{\"symbol\":\"EURUSD\",\"digits\":5,\"point\":0.00010}]}

@router.get(\"/api/candles\")
def api_candles(symbol: str, timeframe: int = 60, limit: int = 300):
    dq = STATE.bars.get((symbol, timeframe), [])
    bars = [b.__dict__ for b in list(dq)[-limit:]]
    return {\"bars\": bars}

@router.get(\"/api/strategies\")
def api_strategies():
    return _loader.discover()

@router.post(\"/api/strategies/enable\")
def api_strat_enable(payload: dict):
    inst = _loader.load(payload[\"id\"])
    ORCH.enable(payload[\"id\"], inst, payload[\"symbol\"], int(payload[\"tf\"]), payload.get(\"settings\", {}))
    return {\"ok\": True}

@router.post(\"/api/strategies/disable\")
def api_strat_disable(payload: dict):
    ORCH.disable(payload[\"id\"], payload[\"symbol\"], int(payload[\"tf\"]))
    return {\"ok\": True}

@router.get(\"/api/signals\")
def api_signals(symbol: str | None = Query(None)):
    # For simplicity returning empty store; extend to actual storage if needed
    return {\"items\": []}

@router.get(\"/api/prediction\")
async def api_prediction(symbol: str, tf: int):
    p = predict(symbol, tf)
    await WS_HUB.broadcast(\"prediction.update\", p.__dict__)
    return p.__dict__
""")

    add("server/server/main.py", """from __future__ import annotations
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from .api.rest import router as rest_router
from .api.bridge import router as bridge_router
from .core.ws import WS_HUB
from .config import settings

app = FastAPI(title=\"Forex Server\")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=[\"*\"],
    allow_headers=[\"*\"],
)

app.include_router(rest_router)
app.include_router(bridge_router)

@app.websocket(\"/ws/market\")
async def ws_market(ws: WebSocket):
    await WS_HUB.register(ws)
    try:
        while True:
            await ws.receive_text()  # keepalive (optional)
    except Exception:
        pass
    finally:
        WS_HUB.unregister(ws)

def create_app():
    return app
""")

    add("server/server/strategies/ema_crossover.py", """from __future__ import annotations
from time import time
from ..core.models import Signal, Bar, Timeframe

def ema(values, n):
    k = 2/(n+1); e = values[0]
    for v in values[1:]: e = v*k + e*(1-k)
    return e

class EmaCrossover:
    id = \"ema_crossover\"
    name = \"EMA Crossover\"
    description = \"Fast/slow EMA cross on close\"
    settingsSchema = {\"fast\": {\"type\":\"number\",\"min\":2,\"max\":50,\"default\":9},
                      \"slow\": {\"type\":\"number\",\"min\":5,\"max\":200,\"default\":21}}

    def on_init(self, ctx): self.ctx = ctx

    def on_bar(self, symbol: str, tf: Timeframe, bar: Bar):
        bars = self.ctx.get_bars(symbol, tf, 200)
        closes = [b.c for b in bars]
        if len(closes) < 50: return []
        fast = ema(closes, int(self.ctx.get_setting(\"fast\", 9)))
        slow = ema(closes, int(self.ctx.get_setting(\"slow\", 21)))
        side = \"BUY\" if fast > slow else \"SELL\"
        sig = Signal(
            id=f\"{self.id}-{int(time())}\",
            time=str(bar.t),
            symbol=symbol,
            strategy=self.id,
            side=side,
            entry=bar.c
        )
        return [sig]

def create():
    return EmaCrossover()
""")

    add("README.md", """# Forex Platform Monorepo

- `frontend/` — Vite + React UI
- `server/` — FastAPI backend (WS + dynamic strategies)

## Run
```bash
# Backend
cd server
python -m pip install -e .  # optional if you make it a package
python -m uvicorn server.main:create_app --factory --reload --port 8000

# Frontend
cd ../frontend
cp .env.example .env
npm i
npm run dev
```

## MT5 Bridge
Point your MT5 EA to POST ticks to `http://127.0.0.1:8000/bridge/tick` and instruments to `/bridge/instruments`.
""")

    write_all(dest, args.overwrite)
    print("\\nDone. Next steps:")
    print("  1) Backend:")
    print("     cd", dest / "server", "&& python -m uvicorn server.main:create_app --factory --reload --port 8000")
    print("  2) Frontend:")
    print("     cd", dest / "frontend", "&& cp .env.example .env && npm i && npm run dev")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
