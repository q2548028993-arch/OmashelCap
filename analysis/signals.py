import logging

import pandas as pd

from analysis.indicators import compute_indicators
from analysis.structure import get_ema_trend, get_trend
from analysis.zones import detect_zone
from data.models import TradeSignal

logger = logging.getLogger(__name__)

# Minimum confluence score required to generate a signal
MIN_SCORE = 3


def evaluate(df: pd.DataFrame, symbol: str) -> TradeSignal:
    """
    Runs the full signal scoring pipeline on the candle DataFrame.
    Returns a TradeSignal with direction and score.

    Scoring rubric (max 5):
      +1  Structure trend (HH/HL or LH/LL)
      +1  EMA alignment confirms trend
      +1  RSI extreme (oversold for CALL, overbought for PUT)
      +1  Price at demand/supply zone
      +1  Bollinger Band touch confirms zone
    """
    no_signal = TradeSignal(
        symbol=symbol,
        direction="NONE",
        score=0,
        reason="Insufficient data",
        trend="RANGE",
        zone="NONE",
        rsi=50.0,
    )

    if len(df) < 50:
        return no_signal

    df = compute_indicators(df)
    last = df.iloc[-1]

    trend = get_trend(df)
    ema_trend = get_ema_trend(df)
    zone = detect_zone(df)

    rsi = float(last.get("rsi", 50))
    close = float(last["close"])
    bb_lower = last.get("bb_lower", None)
    bb_upper = last.get("bb_upper", None)

    # ── Score CALL ────────────────────────────────────────────────────────────
    call_score = 0
    call_reasons = []

    if trend == "UPTREND":
        call_score += 1
        call_reasons.append("structure UPTREND")

    if ema_trend == "UPTREND":
        call_score += 1
        call_reasons.append("EMA aligned bullish")

    if rsi < 35:
        call_score += 1
        call_reasons.append(f"RSI oversold ({rsi:.1f})")

    if zone == "DEMAND":
        call_score += 1
        call_reasons.append("price at demand zone")

    if bb_lower is not None and close <= bb_lower:
        call_score += 1
        call_reasons.append("price at lower BB")

    # ── Score PUT ─────────────────────────────────────────────────────────────
    put_score = 0
    put_reasons = []

    if trend == "DOWNTREND":
        put_score += 1
        put_reasons.append("structure DOWNTREND")

    if ema_trend == "DOWNTREND":
        put_score += 1
        put_reasons.append("EMA aligned bearish")

    if rsi > 65:
        put_score += 1
        put_reasons.append(f"RSI overbought ({rsi:.1f})")

    if zone == "SUPPLY":
        put_score += 1
        put_reasons.append("price at supply zone")

    if bb_upper is not None and close >= bb_upper:
        put_score += 1
        put_reasons.append("price at upper BB")

    # ── Decision ─────────────────────────────────────────────────────────────
    if call_score >= MIN_SCORE and call_score >= put_score:
        return TradeSignal(
            symbol=symbol,
            direction="CALL",
            score=call_score,
            reason=", ".join(call_reasons),
            trend=trend,
            zone=zone,
            rsi=rsi,
        )

    if put_score >= MIN_SCORE and put_score > call_score:
        return TradeSignal(
            symbol=symbol,
            direction="PUT",
            score=put_score,
            reason=", ".join(put_reasons),
            trend=trend,
            zone=zone,
            rsi=rsi,
        )

    return TradeSignal(
        symbol=symbol,
        direction="NONE",
        score=max(call_score, put_score),
        reason=f"Score too low (call={call_score}, put={put_score})",
        trend=trend,
        zone=zone,
        rsi=rsi,
    )
