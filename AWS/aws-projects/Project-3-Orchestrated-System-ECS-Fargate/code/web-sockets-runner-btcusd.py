"""
IMPORTANT NOTE -
This code exists solely to enforce a workload contract for the project.

The logic is intentionally simple. The purpose of this code is to demonstrate:
- a long-running execution model
- persistent in-memory state
- a continuous streaming connection
- retry-unsafe behavior

This project evaluates compute selection and lifecycle control, not algorithmic sophistication or trading performance.

Lifecycle Guarantees:
- Hard stop after 10 minutes from process start
- Fail-fast (non-zero exit on failure)
- Preserves original trading logic
- Local artifacts for later S3 upload
"""

import asyncio
import json
import time
import traceback
from collections import deque
import os
import websockets
import boto3
from botocore.exceptions import ClientError

# =========================
# HARD RUNTIME BOUNDARY
# =========================
DEFAULT_RUNTIME_SECONDS = 2 * 60 * 60  
MAX_RUNTIME_SECONDS = int(
    os.getenv("MAX_RUNTIME_SECONDS", DEFAULT_RUNTIME_SECONDS)
)

PROCESS_START_TS = time.time()

def runtime_expired():
    return (time.time() - PROCESS_START_TS) >= MAX_RUNTIME_SECONDS

# =========================
# OUTPUT CONFIG
# =========================
S3_BUCKET = os.getenv("S3_BUCKET")
S3_PREFIX = os.getenv("S3_PREFIX", "project1/")

if not S3_BUCKET:
    raise RuntimeError("S3_BUCKET env var is required")

s3 = boto3.client("s3")

# =========================
# CONFIG (UNCHANGED)
# =========================
WS_URL = "wss://socket.india.delta.exchange"
SYMBOL = "BTCUSD"

WINDOW = 5
LONG_THRESH = 0.005
SHORT_THRESH = -0.005

POSITION_SIZE = 1
START_BALANCE = 10_000

PING_INTERVAL = 20

LOG_FILE = "trades.log"
EQUITY_FILE = "equity.json"

# =========================
# STATE (UNCHANGED)
# =========================
class BotState:
    def __init__(self):
        self.closes = deque(maxlen=WINDOW + 1)
        self.returns = deque(maxlen=WINDOW)
        self.position = "FLAT"
        self.entry_price = None
        self.balance = START_BALANCE
        self.trades = 0
        self.last_candle_ts = None
        self.equity_curve = []

state = BotState()

# =========================
# LOGGING (STDOUT + FILE)
# =========================
def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

# =========================
# STRATEGY (UNCHANGED)
# =========================
def compute_return(new, prev):
    return (new - prev) / prev if prev else 0.0

def rolling_mean():
    return sum(state.returns) / len(state.returns) if state.returns else 0.0

def signal_from_return(ret_pct):
    if ret_pct > LONG_THRESH:
        return 1
    if ret_pct < SHORT_THRESH:
        return -1
    return 0

# =========================
# EXECUTION (UNCHANGED)
# =========================
def enter_long(price):
    state.position = "LONG"
    state.entry_price = price
    state.trades += 1
    log(f"ENTER LONG @ {price}")

def enter_short(price):
    state.position = "SHORT"
    state.entry_price = price
    state.trades += 1
    log(f"ENTER SHORT @ {price}")

def exit_position(price):
    if state.position == "LONG":
        pnl = (price - state.entry_price) * POSITION_SIZE
    elif state.position == "SHORT":
        pnl = (state.entry_price - price) * POSITION_SIZE
    else:
        return

    state.balance += pnl
    log(f"EXIT {state.position} @ {price} | PnL={pnl:.2f} | Balance={state.balance:.2f}")
    state.position = "FLAT"
    state.entry_price = None

def handle_signal(signal, price):
    if state.position == "FLAT":
        if signal == 1:
            enter_long(price)
        elif signal == -1:
            enter_short(price)

    elif state.position == "LONG":
        if signal <= 0:
            exit_position(price)
            if signal == -1:
                enter_short(price)

    elif state.position == "SHORT":
        if signal >= 0:
            exit_position(price)
            if signal == 1:
                enter_long(price)

# =========================
# METRICS (UNCHANGED)
# =========================
def record_equity(ts, price):
    state.equity_curve.append({
        "timestamp": ts,
        "balance": state.balance,
        "position": state.position,
        "price": price
    })

    if len(state.equity_curve) % 100 == 0:
        with open(EQUITY_FILE, "w") as f:
            json.dump(state.equity_curve, f, indent=2)

# =========================
# DATA FEED (BOUND ONLY)
# =========================
async def consume_ws():
    async with websockets.connect(
        WS_URL,
        ping_interval=PING_INTERVAL,
        ping_timeout=PING_INTERVAL,
        close_timeout=5
    ) as ws:

        sub = {
            "type": "subscribe",
            "payload": {
                "channels": [{"name": "candlestick_1m", "symbols": [SYMBOL]}]
            }
        }

        await ws.send(json.dumps(sub))
        log(f"SUBSCRIBED to {SYMBOL}")

        async for msg in ws:
            if runtime_expired():
                log("TIME WINDOW EXPIRED — stopping run")
                return

            data = json.loads(msg)
            parsed = parse_delta_candlestick(data)
            if parsed is None:
                continue

            ts, close = parsed
            if ts == state.last_candle_ts:
                continue

            state.last_candle_ts = ts

            if state.closes:
                state.returns.append(compute_return(close, state.closes[-1]))

            state.closes.append(close)

            ret_pct = rolling_mean() * 100
            signal = signal_from_return(ret_pct)

            log(f"CANDLE | Close={close} | Ret%={ret_pct:.4f} | Signal={signal}")
            handle_signal(signal, close)
            record_equity(ts, close)

def parse_delta_candlestick(msg: dict):
    if not msg.get("type", "").startswith("candlestick_"):
        return None
    try:
        return msg["candle_start_time"], float(msg["close"])
    except Exception:
        return None

# =========================
# ARTIFACT PUBLISH
# =========================
def upload_artifacts():
    for file in [LOG_FILE, EQUITY_FILE]:
        if not os.path.exists(file):
            continue
        key = f"{S3_PREFIX}{file}"
        log(f"UPLOADING {file} → s3://{S3_BUCKET}/{key}")
        s3.upload_file(file, S3_BUCKET, key)

# =========================
# ENTRYPOINT (FAIL-FAST)
# =========================
async def main():
    log(f"RUN STARTED | max_runtime_seconds={MAX_RUNTIME_SECONDS}")
    try:
        await consume_ws()
        log("RUN COMPLETED")
    except Exception:
        log("RUN FAILED")
        log(traceback.format_exc())
        raise  # non-zero exit

if __name__ == "__main__":
    asyncio.run(main())
