"""
Walk-forward backtest engine.

Strategy is evaluated bar-by-bar on historical candles.
At each bar we ask: "would the signal engine fire here?"
If yes, we simulate the binary option outcome N bars later.

Lookahead note: EMA/RSI/Bollinger are purely backward-looking — no bias.
Swing detection uses a trailing window here (unlike the live engine which
uses center=True for display purposes), keeping the backtest clean.
"""

import logging
import time
from typing import Any

import pandas as pd

from analysis.indicators import compute_indicators
from analysis.structure import get_ema_trend
from analysis.zones import detect_zone
from backtest.fetcher import fetch_candles
from config.settings import settings

logger = logging.getLogger(__name__)

PAYOUT_RATIO = 0.85
MIN_BARS_REQUIRED = 60  # warm-up bars before signals start


def _get_trend_trailing(df: pd.DataFrame) -> str:
    """Market structure using a trailing (non-lookahead) swing window."""
    if len(df) < 20:
        return "RANGE"

    lookback = 5
    highs = df["high"].rolling(window=lookback).max()
    lows = df["low"].rolling(window=lookback).min()

    sh = df[df["high"] == highs]["high"].dropna().values
    sl = df[df["low"] == lows]["low"].dropna().values

    if len(sh) < 2 or len(sl) < 2:
        return "RANGE"

    hh = sh[-1] > sh[-2]
    hl = sl[-1] > sl[-2]
    lh = sh[-1] < sh[-2]
    ll = sl[-1] < sl[-2]

    if hh and hl:
        return "UPTREND"
    if lh and ll:
        return "DOWNTREND"
    return "RANGE"


def _score_row(df_window: pd.DataFrame, symbol: str) -> tuple[str, int, str]:
    """Returns (direction, score, reason) for the last bar in df_window."""
    if len(df_window) < MIN_BARS_REQUIRED:
        return "NONE", 0, "warm-up"

    df = compute_indicators(df_window)
    last = df.iloc[-1]

    trend = _get_trend_trailing(df)
    ema_trend = get_ema_trend(df)
    zone = detect_zone(df)

    rsi = float(last.get("rsi", 50) or 50)
    close = float(last["close"])
    bb_lower = last.get("bb_lower")
    bb_upper = last.get("bb_upper")

    call_score, call_reasons = 0, []
    put_score, put_reasons = 0, []

    if trend == "UPTREND":
        call_score += 1
        call_reasons.append("structure UPTREND")
    if trend == "DOWNTREND":
        put_score += 1
        put_reasons.append("structure DOWNTREND")

    if ema_trend == "UPTREND":
        call_score += 1
        call_reasons.append("EMA bullish")
    if ema_trend == "DOWNTREND":
        put_score += 1
        put_reasons.append("EMA bearish")

    if rsi < 35:
        call_score += 1
        call_reasons.append(f"RSI {rsi:.0f}")
    if rsi > 65:
        put_score += 1
        put_reasons.append(f"RSI {rsi:.0f}")

    if zone == "DEMAND":
        call_score += 1
        call_reasons.append("demand zone")
    if zone == "SUPPLY":
        put_score += 1
        put_reasons.append("supply zone")

    if bb_lower is not None and not pd.isna(bb_lower) and close <= float(bb_lower):
        call_score += 1
        call_reasons.append("lower BB")
    if bb_upper is not None and not pd.isna(bb_upper) and close >= float(bb_upper):
        put_score += 1
        put_reasons.append("upper BB")

    min_score = settings.MIN_SCORE if hasattr(settings, "MIN_SCORE") else 3

    if call_score >= min_score and call_score >= put_score:
        return "CALL", call_score, ", ".join(call_reasons)
    if put_score >= min_score and put_score > call_score:
        return "PUT", put_score, ", ".join(put_reasons)
    return "NONE", max(call_score, put_score), "no confluence"


async def run(
    symbol: str,
    granularity: int,
    count: int,
    trade_duration_bars: int,
    starting_balance: float,
    min_score: int = 3,
) -> dict[str, Any]:
    t0 = time.monotonic()

    df = await fetch_candles(symbol, granularity, count)
    if df.empty or len(df) < MIN_BARS_REQUIRED + trade_duration_bars + 10:
        return {"error": "Not enough candle data to run backtest"}

    balance = starting_balance
    trades: list[dict] = []
    equity_curve: list[dict] = [{"time": int(df.iloc[0]["epoch"]), "value": round(balance, 2)}]
    open_until: int = -1  # bar index when current trade expires (no overlapping trades)

    for i in range(MIN_BARS_REQUIRED, len(df) - trade_duration_bars):
        if i <= open_until:
            continue

        direction, score, reason = _score_row(df.iloc[: i + 1], symbol)

        if direction == "NONE" or score < min_score:
            continue

        entry_close = float(df.iloc[i]["close"])
        exit_close = float(df.iloc[i + trade_duration_bars]["close"])
        entry_epoch = int(df.iloc[i]["epoch"])
        exit_epoch = int(df.iloc[i + trade_duration_bars]["epoch"])

        stake = max(
            settings.MIN_STAKE,
            min(round(balance * settings.RISK_PER_TRADE, 2), settings.MAX_STAKE),
        )

        is_win = (exit_close > entry_close) if direction == "CALL" else (exit_close < entry_close)
        profit = round(stake * PAYOUT_RATIO if is_win else -stake, 2)
        balance = round(balance + profit, 2)

        open_until = i + trade_duration_bars

        trades.append(
            {
                "bar": i,
                "entry_epoch": entry_epoch,
                "exit_epoch": exit_epoch,
                "direction": direction,
                "score": score,
                "reason": reason,
                "stake": stake,
                "entry": entry_close,
                "exit": exit_close,
                "profit": profit,
                "is_win": is_win,
                "balance": balance,
            }
        )

        equity_curve.append({"time": exit_epoch, "value": balance})

    elapsed = round(time.monotonic() - t0, 2)
    return _build_report(
        trades, equity_curve, starting_balance, balance, symbol, granularity, count, elapsed
    )


def _build_report(
    trades: list[dict],
    equity_curve: list[dict],
    starting_balance: float,
    final_balance: float,
    symbol: str,
    granularity: int,
    candle_count: int,
    elapsed: float,
) -> dict[str, Any]:
    total = len(trades)

    if total == 0:
        return {
            "symbol": symbol,
            "granularity": granularity,
            "candle_count": candle_count,
            "total_trades": 0,
            "message": "No signals fired — strategy produced no trades on this data",
            "equity_curve": equity_curve,
            "elapsed_s": elapsed,
        }

    wins = sum(1 for t in trades if t["is_win"])
    losses = total - wins
    win_rate = round(wins / total, 4)

    profits = [t["profit"] for t in trades]
    gross_wins = sum(p for p in profits if p > 0)
    gross_losses = abs(sum(p for p in profits if p < 0))
    total_pnl = round(sum(profits), 2)
    avg_win = round(gross_wins / wins, 2) if wins > 0 else 0.0
    avg_loss = round(gross_losses / losses, 2) if losses > 0 else 0.0
    profit_factor = round(gross_wins / gross_losses, 3) if gross_losses > 0 else float("inf")
    expectancy = round(win_rate * avg_win - (1 - win_rate) * avg_loss, 4)

    # Max drawdown from equity curve
    peak = starting_balance
    max_dd = 0.0
    for point in equity_curve:
        v = point["value"]
        if v > peak:
            peak = v
        dd = (peak - v) / peak
        if dd > max_dd:
            max_dd = dd
    max_dd_pct = round(max_dd * 100, 2)

    # Return on account
    roi = round((final_balance - starting_balance) / starting_balance * 100, 2)

    # Best/worst
    best = round(max(profits), 2)
    worst = round(min(profits), 2)

    # Max consecutive wins/losses
    max_consec_wins = max_consec_losses = cur_w = cur_l = 0
    for t in trades:
        if t["is_win"]:
            cur_w += 1
            cur_l = 0
        else:
            cur_l += 1
            cur_w = 0
        max_consec_wins = max(max_consec_wins, cur_w)
        max_consec_losses = max(max_consec_losses, cur_l)

    return {
        "symbol": symbol,
        "granularity": granularity,
        "candle_count": candle_count,
        "elapsed_s": elapsed,
        "starting_balance": starting_balance,
        "final_balance": round(final_balance, 2),
        "roi_pct": roi,
        "total_trades": total,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "win_rate_pct": round(win_rate * 100, 2),
        "total_pnl": total_pnl,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
        "expectancy_per_trade": expectancy,
        "max_drawdown_pct": max_dd_pct,
        "best_trade": best,
        "worst_trade": worst,
        "max_consec_wins": max_consec_wins,
        "max_consec_losses": max_consec_losses,
        "equity_curve": equity_curve,
        "trades": trades[-50:],  # last 50 trades for display
    }
