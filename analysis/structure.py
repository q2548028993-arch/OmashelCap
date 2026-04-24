import logging
from typing import List, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

# Number of candles to look back for swing detection
SWING_LOOKBACK = 5


def find_swings(df: pd.DataFrame, lookback: int = SWING_LOOKBACK) -> pd.DataFrame:
    """
    Marks swing highs and swing lows on the DataFrame.
    A swing high: highest high in the surrounding window.
    A swing low:  lowest low in the surrounding window.
    """
    df = df.copy()
    df["swing_high"] = df["high"].rolling(window=lookback * 2 + 1, center=True).max() == df["high"]
    df["swing_low"] = df["low"].rolling(window=lookback * 2 + 1, center=True).min() == df["low"]
    return df


def get_trend(df: pd.DataFrame) -> str:
    """
    Detects market structure trend using Higher Highs / Higher Lows logic.
    Returns: "UPTREND" | "DOWNTREND" | "RANGE"
    """
    if len(df) < 20:
        return "RANGE"

    df = find_swings(df)
    swing_highs = df[df["swing_high"]]["high"].dropna().values
    swing_lows = df[df["swing_low"]]["low"].dropna().values

    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return "RANGE"

    hh = swing_highs[-1] > swing_highs[-2]   # Higher High
    hl = swing_lows[-1] > swing_lows[-2]      # Higher Low
    lh = swing_highs[-1] < swing_highs[-2]    # Lower High
    ll = swing_lows[-1] < swing_lows[-2]      # Lower Low

    if hh and hl:
        return "UPTREND"
    elif lh and ll:
        return "DOWNTREND"
    return "RANGE"


def get_ema_trend(df: pd.DataFrame) -> str:
    """
    Secondary trend confirmation using EMA alignment.
    EMA9 > EMA21 > EMA50 → UPTREND; inverse → DOWNTREND.
    """
    if "ema_9" not in df.columns or "ema_50" not in df.columns:
        return "RANGE"

    last = df.iloc[-1]
    try:
        ema9, ema21, ema50 = last["ema_9"], last["ema_21"], last["ema_50"]
        if ema9 > ema21 > ema50:
            return "UPTREND"
        elif ema9 < ema21 < ema50:
            return "DOWNTREND"
    except (KeyError, TypeError):
        pass
    return "RANGE"


def get_recent_swing_levels(df: pd.DataFrame) -> Tuple[float, float]:
    """
    Returns (last_swing_high, last_swing_low) for use as TP/SL reference.
    """
    df = find_swings(df)
    highs = df[df["swing_high"]]["high"].dropna()
    lows = df[df["swing_low"]]["low"].dropna()

    last_high = highs.iloc[-1] if len(highs) > 0 else df["high"].max()
    last_low = lows.iloc[-1] if len(lows) > 0 else df["low"].min()
    return float(last_high), float(last_low)
