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
    if bb is not None:
        df["bb_upper"] = bb["BBU_20_2.0"]
        df["bb_lower"] = bb["BBL_20_2.0"]
        df["bb_mid"] = bb["BBM_20_2.0"]

    # MACD
    macd = ta.macd(df["close"], fast=12, slow=26, signal=9)
    if macd is not None:
        df["macd"] = macd["MACD_12_26_9"]
        df["macd_signal"] = macd["MACDs_12_26_9"]
        df["macd_hist"] = macd["MACDh_12_26_9"]

    # ATR for volatility / stop-loss sizing
    df["atr"] = ta.atr(df["high"], df["low"], df["close"], length=14)

    return df
