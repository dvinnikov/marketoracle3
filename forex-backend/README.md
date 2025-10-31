# Forex Backend

FastAPI backend that bridges MT5 (via EA HTTP posts) to a React/Vite UI.
- REST: instruments, candles, strategies (dynamic), signals, prediction
- WS: price.tick, bar.update, signal.new
- Bridge: tick/account/positions/orders/instruments/status
- Commands: server→EA queue with fetch/ack

## Run
```bash
python -m uvicorn server.main:create_app --factory --reload --port 8000
```

## MT5 EA endpoints (POST)
- /bridge/tick
- /bridge/account
- /bridge/positions
- /bridge/orders
- /bridge/instruments
- /bridge/status
- /bridge/commands/fetch   (from commands router, not prefixed twice)
- /bridge/commands/ack

## UI endpoints
- GET /api/instruments
- GET /api/candles?symbol=EURUSD&timeframe=60&limit=300
- GET /api/strategies
- POST /api/strategies/enable  {id,symbol,tf,settings}
- POST /api/strategies/disable {id,symbol,tf}
- GET /api/signals?symbol=EURUSD
- GET /api/prediction?symbol=EURUSD&tf=60

WebSocket:
- ws://127.0.0.1:8000/ws/market  → messages with {topic, data}
  - topic=price.tick, bar.update, signal.new
