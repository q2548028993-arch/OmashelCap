"""
Fetch historical OHLC candles from Deriv's WebSocket API.
Falls back to synthetic Brownian-motion candles when USE_MOCK=true or connection fails.
"""
import json
import logging
import math
import os
import random

import pandas as pd
import websockets

from config.settings import settings

logger = logging.getLogger(__name__)

_USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"


async def fetch_candles(symbol: str, granularity: int, count: int) -> pd.DataFrame:
    """
    Returns a DataFrame with columns [epoch, open, high, low, close].
    Attempts Deriv WS first; falls back to synthetic data on any failure.
    """
    if _USE_MOCK or not settings.APP_ID or not settings.API_TOKEN:
        logger.info("Using synthetic candle data for backtest")
        return _synthetic_candles(symbol, granularity, count)

    try:
        return await _fetch_from_deriv(symbol, granularity, count)
    except Exception as e:
        logger.warning(f"Deriv fetch failed ({e}) — falling back to synthetic data")
        return _synthetic_candles(symbol, granularity, count)


async def _fetch_from_deriv(symbol: str, granularity: int, count: int) -> pd.DataFrame:
    url = f"wss://ws.derivws.com/websockets/v3?app_id={settings.APP_ID}"
    async with websockets.connect(url, ping_interval=None) as ws:
        await ws.send(json.dumps({
            "ticks_history": symbol,
            "adjust_start_time": 1,
            "count": count,
            "end": "latest",
            "start": 1,
            "style": "candles",
            "granularity": granularity,
        }))
        raw = json.loads(await ws.recv())

    if "error" in raw:
        raise RuntimeError(raw["error"]["message"])

    candles = raw.get("candles", [])
    if not candles:
        raise RuntimeError("Empty candle response")

    df = pd.DataFrame(candles, columns=["epoch", "open", "high", "low", "close"])
    for col in ["open", "high", "low", "close"]:
        df[col] = df[col].astype(float)
    df["epoch"] = df["epoch"].astype(int)

    logger.info(f"Fetched {len(df)} candles for {symbol} ({granularity}s) from Deriv")
    return df.reset_index(drop=True)


def _synthetic_candles(symbol: str, granularity: int, count: int) -> pd.DataFrame:
    """Geometric Brownian Motion synthetic OHLC — realistic enough for strategy testing."""
    # Volatility calibrated per symbol
    vol_map = {
        "R_10": 0.0003, "R_25": 0.0006, "R_50": 0.001,
        "R_75": 0.0018, "R_100": 0.0025,
    }
    drift = 0.0
    sigma = vol_map.get(symbol, 0.001)

    import time
    end_epoch = int(time.time()) - granularity
    start_price = 1000.0 + random.uniform(-200, 200)

    rows = []
    price = start_price
    for i in range(count):
        epoch = end_epoch - (count - i - 1) * granularity
        ret = drift + sigma * random.gauss(0, 1)
        o = price
        c = round(o * math.exp(ret), 5)
        h = round(max(o, c) * (1 + abs(random.gauss(0, sigma * 0.5))), 5)
        l = round(min(o, c) * (1 - abs(random.gauss(0, sigma * 0.5))), 5)
        rows.append({"epoch": epoch, "open": o, "high": h, "low": l, "close": c})
        price = c

    logger.info(f"Generated {count} synthetic candles for {symbol}")
    return pd.DataFrame(rows)
