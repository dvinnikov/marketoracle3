# Forex Backend + MT5 Bridge

A modular **FastAPI** backend that receives live data from **MetaTrader 5 (MT5)** via an Expert Advisor (EA), aggregates candles across timeframes, runs **pluggable strategies**, produces **predictions**, and streams everything to a **React + Vite** UI via WebSocket and REST. It also exposes a **command queue** to send trade commands from the server/UI to the EA.

---

## Contents
- [Folder structure](#folder-structure)
- [Prerequisites](#prerequisites)
- [Quick start (Windows)](#quick-start-windows)
- [Running the backend](#running-the-backend)
- [Running the MT5 EA (Bridge)](#running-the-mt5-ea-bridge)
- [How it works](#how-it-works)
- [API overview](#api-overview)
- [Strategies: add/enable/disable](#strategies-addenabledisable)
- [Predictions](#predictions)
- [WebSocket messages](#websocket-messages)
- [UDF (TradingView-like) endpoints](#udf-tradingview-like-endpoints)
- [Server → EA command queue](#server--ea-command-queue)
- [Testing script](#testing-script)
- [Troubleshooting](#troubleshooting)

---

## Folder structure

```
forex-backend/
├─ pyproject.toml
└─ server/
   ├─ __init__.py
   ├─ main.py                  # FastAPI factory + router wiring
   ├─ config.py                # settings (CORS, strategies dir, TF map)
   ├─ api/
   │  ├─ __init__.py
   │  ├─ rest.py               # /api/* endpoints
   │  ├─ bridge.py             # /bridge/* endpoints (EA → server)
   │  ├─ commands.py           # /api/commands/* and /bridge/commands/*
   │  └─ udf.py                # /udf/* minimal TradingView compatibility
   ├─ core/
   │  ├─ models.py             # Bar/Tick/Signal/Prediction dataclasses
   │  ├─ state.py              # in-memory storage for ticks/bars/account/etc
   │  ├─ bars.py               # multi-timeframe bar aggregator
   │  ├─ ws.py                 # WebSocket hub (broadcasts events)
   │  ├─ indicators.py         # SMA/EMA/RSI helpers
   │  ├─ loader.py             # dynamic strategy discovery/loader
   │  ├─ orchestrator.py       # runs strategies on bar close
   │  ├─ prediction.py         # simple target/confidence model
   │  └─ storage.py            # signal logs, in-memory
   └─ strategies/              # plugin strategies (*.py)
      ├─ ema_crossover.py
      ├─ range_fade.py
      ├─ bollinger_bounce.py
      ├─ support_resistance.py
      ├─ breakout.py
      ├─ fibonacci_retracement.py
      └─ price_action.py
```

---

## Prerequisites

- Python **3.10+**
- MT5 terminal (for the EA)
- (Optional) Node 18+ for the React/Vite app
- Windows users: **PowerShell** or **Git Bash**

---

## Quick start (Windows)

```powershell
# go to project root (folder with pyproject.toml)
cd "C:\Path\to\forex-backend"

# create & activate venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # PowerShell
# source .venv/Scripts/activate  # Git Bash

# install in editable mode
python -m pip install -e .

# run
python -m uvicorn server.main:create_app --factory --reload --port 8000
# then open http://127.0.0.1:8000/healthz
```

> **Tip:** If you run from outside the project root, add `--app-dir "C:\Path\to\forex-backend"`.

---

## Running the backend

- REST root: `http://127.0.0.1:8000`
- WebSocket: `ws://127.0.0.1:8000/ws/market`

You should see `{"ok": true, ...}` at `/healthz`. The server is empty until the EA (or test script) posts instruments, ticks and snapshots.

---

## UI configuration (.env)

The React/Vite UI reads the backend URLs from environment variables. Create `ui/.env` (or `.env.local`) with:

```
VITE_BACKEND_BASE=http://127.0.0.1:8000
VITE_BACKEND_WS=ws://127.0.0.1:8000/ws/market
```

Restart the dev server after changing these values so Vite can pick them up.

---

## Running the MT5 EA (Bridge)

1. Open MetaTrader 5 → **MetaEditor**.
2. Create a new Expert Advisor (or use the provided MQL5 file).
3. Paste the EA code (see **EA Bridge** below) into the editor.
4. Set input `BASE_URL` to your server base (default `http://127.0.0.1:8000`).
5. Compile and attach EA to a chart (e.g., EURUSD M1).

**EA Bridge responsibilities**

- Sends every tick to `/bridge/tick`:
  ```json
  {"symbol":"EURUSD","bid":1.10001,"ask":1.10011,"time":1700000000}
  ```
- Periodically sends snapshots:
  - `/bridge/account` (balance/equity/etc)
  - `/bridge/positions`
  - `/bridge/orders`
  - `/bridge/instruments` (once on init; all symbols and their precision)
- Polls for commands:
  - `/bridge/commands/fetch` → list of pending commands
  - Executes them (market/modify/close), then `/bridge/commands/ack`

**Minimal EA snippet (already provided in your project):**
```mql5
input string BASE_URL="http://127.0.0.1:8000";
// OnTick() → POST /bridge/tick
// OnInit()  → POST /bridge/instruments
// every SNAPSHOT_MS → POST /bridge/account|positions|orders
// PollCommands()    → POST /bridge/commands/fetch|ack
```

> If you need the full EA file again, see `MT5BridgePro_Compat.mq5` in your notes (the version that avoids PositionSelectByIndex and supports command polling).

---

## How it works

1. **EA → Server**  
   Ticks and snapshots are posted to `/bridge/*`.  
   The server aggregates ticks into **bars** for multiple timeframes (1/5/15/60m).

2. **Strategy Orchestrator**  
   On **bar close**, the orchestrator runs **enabled strategies** for the (symbol, timeframe) and appends any **signals** to the log, broadcasting `signal.new` to WebSocket clients.

3. **UI (React/Vite)**  
   Subscribes to `ws://…/ws/market` and listens for:
   - `price.tick` for live price
   - `bar.update` for candles
   - `signal.new` for new strategy signals

4. **Prediction**  
   `/api/prediction?symbol=…&tf=…` computes a simple near-term target + confidence (demo module; replace with your model if needed).

5. **Server → EA commands**  
   The UI can enqueue market/modify/close via `/api/commands/*`.  
   The EA periodically fetches and executes them, then ACKs with success/fail status.

---

## API overview

### Bridge (EA → Server)
- `POST /bridge/instruments` `{symbols:[{symbol, digits, point}]}`
- `POST /bridge/tick` `{symbol, bid, ask, time}`
- `POST /bridge/account` `{login, name, server, currency, balance, equity, margin}`
- `POST /bridge/positions` `{positions:[{ticket, symbol, type, volume, price, sl, tp, profit, time}]}`
- `POST /bridge/orders` `{orders:[{ticket, symbol, type, volume, price, sl, tp, time}]}`
- `POST /bridge/status` `{status:"started"|"stopped"}`

### REST (UI ←→ Server)
- `GET  /healthz`
- `GET  /api/instruments`
- `GET  /api/candles?symbol=EURUSD&timeframe=60&limit=300`
- `GET  /api/strategies` → discovered plugin list
- `POST /api/strategies/enable` `{"id","symbol","tf","settings":{...}}`
- `POST /api/strategies/disable` `{"id","symbol","tf"}`
- `GET  /api/signals?symbol=EURUSD`
- `GET  /api/prediction?symbol=EURUSD&tf=60`

### Commands
- `POST /api/commands/market` `{"symbol","side":"buy|sell","volume", "sl","tp"}`
- `POST /api/commands/modify` `{"ticket","sl","tp"}`
- `POST /api/commands/close`  `{"ticket"}`
- `POST /bridge/commands/fetch` `{"after":<last_id>}`
- `POST /bridge/commands/ack`   `{"id", "ok":true|false}`

---

## Strategies: add/enable/disable

- A **strategy** is a Python file in `server/strategies/*.py` exposing `create()` that returns an object with:
  - `id`, `name`, `description`, `settingsSchema`
  - `on_init(ctx)`: called once
  - `on_bar(symbol, tf, bar) -> list[Signal]`: called on **bar close**
- The loader imports them as `server.strategies.<file_stem>` so relative imports work.

**Example skeleton**
```python
# server/strategies/my_strategy.py
from server.core.models import Signal, Bar, Timeframe

class MyStrategy:
    id = "my_strategy"
    name = "My Strategy"
    description = "…"
    settingsSchema = {"period":{"type":"number","default":20}}

    def on_init(self, ctx): self.ctx = ctx

    def on_bar(self, symbol: str, tf: Timeframe, bar: Bar):
        bars = self.ctx.get_bars(symbol, tf, 200)
        # compute …
        return []  # or [Signal(...)]

def create(): return MyStrategy()
```

**Enable at runtime**
```http
POST /api/strategies/enable
{"id":"my_strategy","symbol":"EURUSD","tf":60,"settings":{"period":30}}
```

---

## Predictions

`GET /api/prediction?symbol=EURUSD&tf=60` returns:
```json
{"symbol":"EURUSD","tf":60,"target":1.10123,"confidence":0.62}
```
This demo model uses slope/volatility; swap in your own logic in `server/core/prediction.py`.

---

## WebSocket messages

`ws://127.0.0.1:8000/ws/market` emits JSON envelopes:
```json
{"type":"price.tick","data":{"symbol":"EURUSD","bid":1.10001,"ask":1.10011,"time":1700000000}}
{"type":"bar.update","data":{"symbol":"EURUSD","tf":60,"bar":{"t":1700000000,"o":...,"h":...,"l":...,"c":...,"v":0}}}
{"type":"signal.new","data":{ /* Signal */ }}
```

---

## UDF (TradingView-like) endpoints

- `GET /udf/symbols?symbol=EURUSD`
- `GET /udf/history?symbol=EURUSD&resolution=60&from=...&to=...`

Responses mimic TradingView UDF for easy chart adapters.

---

## Server → EA command queue

1. UI/REST enqueues commands at `/api/commands/*`.
2. EA polls `/bridge/commands/fetch` with `{"after": <last_ack_id>}`.
3. EA executes the command (market/modify/close).
4. EA ACKs back to `/bridge/commands/ack` with `{"id":..., "ok":true|false}`.

This cycle is stateless and robust (EA can reconnect any time).

---

## Testing script

We provide two scripts:

- `test_backend.py` – full test
- `test_backend_local.py` – same, but **ignores system proxies**

Run:
```bash
python test_backend_local.py --base http://127.0.0.1:8000 --symbol EURUSD --tf 60
```

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'server'`**  
Run Uvicorn from the project root or pass `--app-dir`:
```
python -m uvicorn --app-dir "C:\Path\to\forex-backend" server.main:create_app --factory --reload --port 8000
```

**`ImportError: attempted relative import with no known parent package` (strategies)**  
The loader must import as `server.strategies.<name>`. Use the provided `loader.py` (Option 1).

**Proxy errors when calling localhost**  
Unset proxy env vars or use `test_backend_local.py` which disables proxies:
```
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
export NO_PROXY=127.0.0.1,localhost
```

**403 on WebSocket**  
Usually CORS/Origin mismatch or wrong path. Use `ws://127.0.0.1:8000/ws/market` and keep the default CORS origins in `config.py`.

**No candles returned**  
Bars are created from ticks. Ensure the EA (or test script) is posting ticks across at least **2 bar intervals** for the requested timeframe.

---

## License
MIT (adjust as needed).
