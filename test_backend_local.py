#!/usr/bin/env python3
"""
Local-only API test that IGNORES system proxy settings.
Use this if requests tries to go through a corporate proxy and fails.

Run:
  python test_backend_local.py --base http://127.0.0.1:8000 --symbol EURUSD --tf 60
"""
from __future__ import annotations
import argparse, time, sys, os
from typing import Any, Dict

try:
    import requests
except ImportError:
    print("This script requires 'requests'. Install it:\n  python -m pip install requests")
    sys.exit(1)

# --- kill proxies so localhost won't be proxied ---
for k in ["HTTP_PROXY","http_proxy","HTTPS_PROXY","https_proxy"]:
    os.environ.pop(k, None)
os.environ["NO_PROXY"] = "127.0.0.1,localhost"

# Use a session that does NOT read env proxies
SESSION = requests.Session()
SESSION.trust_env = False
PROXIES = {"http": None, "https": None}

BOLD = "\033[1m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def log_pass(msg: str): print(f"{GREEN}[PASS]{RESET} {msg}")
def log_fail(msg: str, detail: str = ""):
    print(f"{RED}[FAIL]{RESET} {msg}")
    if detail: print(detail)
def log_info(msg: str): print(f"{YELLOW}[INFO]{RESET} {msg}")

def post(base: str, path: str, payload: Dict[str, Any]):
    url = base + path
    return SESSION.post(url, json=payload, timeout=10, proxies=PROXIES)

def get(base: str, path: str, params: Dict[str, Any] | None = None):
    url = base + path
    return SESSION.get(url, params=params, timeout=10, proxies=PROXIES)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    ap.add_argument("--symbol", default="EURUSD")
    ap.add_argument("--tf", type=int, default=60)
    args = ap.parse_args()

    BASE = args.base.rstrip("/")
    SYMBOL = args.symbol
    TF = int(args.tf)

    # -------- HEALTH --------
    r = get(BASE, "/healthz")
    if r.ok and r.json().get("ok"):
        log_pass(f"GET /healthz -> {r.json()}")
    else:
        log_fail("GET /healthz", r.text); return 1

    # -------- BRIDGE: instruments --------
    r = post(BASE, "/bridge/instruments", {"symbols":[{"symbol": SYMBOL, "digits":5, "point":0.00010}]})
    if r.ok: log_pass("POST /bridge/instruments (1)")
    else: log_fail("POST /bridge/instruments", r.text); return 1

    # -------- BRIDGE: account --------
    r = post(BASE, "/bridge/account", {
        "login": 1, "name": "Local", "server":"MT5-Demo", "currency":"USD",
        "balance": 10000.0, "equity": 10000.0, "margin": 0.0
    })
    if r.ok: log_pass("POST /bridge/account")
    else: log_fail("POST /bridge/account", r.text); return 1

    # -------- Ticks to build bars --------
    now = int(time.time())
    ticks = [
        {"symbol": SYMBOL, "bid": 1.10000, "ask": 1.10010, "time": now},
        {"symbol": SYMBOL, "bid": 1.10020, "ask": 1.10030, "time": now + 5},
        {"symbol": SYMBOL, "bid": 1.10010, "ask": 1.10020, "time": now + 10},
        {"symbol": SYMBOL, "bid": 1.10040, "ask": 1.10050, "time": now + 65},
        {"symbol": SYMBOL, "bid": 1.10060, "ask": 1.10070, "time": now + 70},
    ]
    for t in ticks:
        r = post(BASE, "/bridge/tick", t)
        if not r.ok: log_fail("POST /bridge/tick", r.text); return 1
    log_pass(f"POST /bridge/tick x{len(ticks)}")
    time.sleep(0.15)

    # -------- REST: candles --------
    r = get(BASE, "/api/candles", {"symbol": SYMBOL, "timeframe": TF, "limit": 100})
    if r.ok: log_pass(f"GET /api/candles -> {len(r.json().get('bars', []))} bars")
    else: log_fail("GET /api/candles", r.text); return 1

    # -------- Strategies --------
    r = get(BASE, "/api/strategies")
    if not r.ok: log_fail("GET /api/strategies", r.text); return 1
    strategies = r.json()
    log_pass(f"GET /api/strategies -> {len(strategies)}")
    if strategies:
        sid = strategies[0]["id"]
        r = post(BASE, "/api/strategies/enable", {"id": sid, "symbol": SYMBOL, "tf": TF, "settings": {}})
        if r.ok: log_pass(f"enabled {sid}")
        else: log_fail("enable strategy", r.text); return 1
        r = get(BASE, "/api/prediction", {"symbol": SYMBOL, "tf": TF})
        if r.ok: log_pass(f"prediction -> {r.json()}")
        r = get(BASE, "/api/signals", {"symbol": SYMBOL})
        if r.ok: log_pass(f"signals -> {len(r.json().get('items', []))}")
        post(BASE, "/api/strategies/disable", {"id": sid, "symbol": SYMBOL, "tf": TF})

    # -------- UDF --------
    r = get(BASE, "/udf/symbols", {"symbol": SYMBOL})
    if r.ok: log_pass("/udf/symbols ok")
    r = get(BASE, "/udf/history", {"symbol": SYMBOL, "resolution": str(TF), "from": now-120, "to": now+120})
    if r.ok: log_pass(f"/udf/history -> {r.json().get('s')}")

    # -------- Commands queue --------
    r = post(BASE, "/api/commands/market", {"symbol": SYMBOL, "side":"buy", "volume":0.1})
    if r.ok: log_pass("enqueued market order")
    r = post(BASE, "/bridge/commands/fetch", {"after": 0})
    if r.ok:
        cmds = r.json().get("commands", [])
        log_pass(f"fetched {len(cmds)} commands")
        for c in cmds:
            post(BASE, "/bridge/commands/ack", {"id": c["id"], "ok": True})
        log_pass("acked all")

    print(f"\n{BOLD}{GREEN}Local API checks completed (no proxy).{RESET}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
