import logging

import pandas as pd
import pandas_ta as ta

logger = logging.getLogger(__name__)


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes all technical indicators on the candle DataFrame.
    Returns df with new columns appended in-place.
    Requires columns: open, high, low, close
    """
    if len(df) < 30:
        return df

    df = df.copy()

    # Trend
    df["ema_9"] = ta.ema(df["close"], length=9)
    df["ema_21"] = ta.ema(df["close"], length=21)
    df["ema_50"] = ta.ema(df["close"], length=50)

    # Momentum
    df["rsi"] = ta.rsi(df["close"], length=14)

    # Bollinger Bands
    bb = ta.bbands(df["close"], length=20, std=2)
    if bb is not None and not bb.empty:
        cols = bb.columns.tolist()
        upper = next((c for c in cols if c.startswith("BBU")), None)
        lower = next((c for c in cols if c.startswith("BBL")), None)
        mid   = next((c for c in cols if c.startswith("BBM")), None)
        if upper:
            df["bb_upper"] = bb[upper]
        if lower:
            df["bb_lower"] = bb[lower]
        if mid:
            df["bb_mid"] = bb[mid]

    # MACD
    macd = ta.macd(df["close"], fast=12, slow=26, signal=9)
    if macd is not None and not macd.empty:
        cols = macd.columns.tolist()
        m   = next((c for c in cols if c.startswith("MACD_")), None)
        ms  = next((c for c in cols if c.startswith("MACDs_")), None)
        mh  = next((c for c in cols if c.startswith("MACDh_")), None)
        if m:
            df["macd"] = macd[m]
        if ms:
            df["macd_signal"] = macd[ms]
        if mh:
            df["macd_hist"] = macd[mh]

    # ATR for volatility / stop-loss sizing
    df["atr"] = ta.atr(df["high"], df["low"], df["close"], length=14)

    return df
