import logging

import pandas as pd

logger = logging.getLogger(__name__)

# Minimum candle body size (as fraction of recent ATR) to qualify as a zone origin
ZONE_STRENGTH_MULTIPLIER = 1.5


def detect_zone(df: pd.DataFrame) -> str:
    """
    Detects if the current price is near a supply or demand zone.

    Demand zone: strong bullish candle origin (price moved up sharply from this level).
    Supply zone: strong bearish candle origin (price moved down sharply from this level).

    Returns: "DEMAND" | "SUPPLY" | "NONE"
    """
    if len(df) < 10 or "atr" not in df.columns:
        return "NONE"

    current_price = df["close"].iloc[-1]
    atr = df["atr"].dropna().iloc[-1]
    threshold = atr * ZONE_STRENGTH_MULTIPLIER

    # Look at the last 20 candles for zone origins
    lookback = df.tail(20)

    for _, candle in lookback.iterrows():
        body = abs(candle["close"] - candle["open"])
        if body < threshold:
            continue

        # Demand zone: strong bullish move; current price is pulling back to origin
        if candle["close"] > candle["open"]:
            zone_top = max(candle["open"], candle["close"])
            zone_bottom = min(candle["open"], candle["close"])
            if zone_bottom <= current_price <= zone_top + atr:
                return "DEMAND"

        # Supply zone: strong bearish move; current price is retracing up to origin
        if candle["close"] < candle["open"]:
            zone_top = max(candle["open"], candle["close"])
            zone_bottom = min(candle["open"], candle["close"])
            if zone_bottom - atr <= current_price <= zone_top:
                return "SUPPLY"

    return "NONE"


def get_zone_boundaries(df: pd.DataFrame, zone_type: str) -> tuple | None:
    """
    Returns (zone_low, zone_high) for the most recent zone of zone_type.
    Used by risk manager to set TP near the zone boundary.
    """
    if len(df) < 10 or "atr" not in df.columns:
        return None

    atr = df["atr"].dropna().iloc[-1]
    threshold = atr * ZONE_STRENGTH_MULTIPLIER
    lookback = df.tail(20)

    for _, candle in reversed(list(lookback.iterrows())):
        body = abs(candle["close"] - candle["open"])
        if body < threshold:
            continue

        is_bullish = candle["close"] > candle["open"]
        is_bearish = candle["close"] < candle["open"]

        if zone_type == "DEMAND" and is_bullish:
            return (
                float(min(candle["open"], candle["close"])),
                float(max(candle["open"], candle["close"])),
            )
        if zone_type == "SUPPLY" and is_bearish:
            return (
                float(min(candle["open"], candle["close"])),
                float(max(candle["open"], candle["close"])),
            )

    return None
