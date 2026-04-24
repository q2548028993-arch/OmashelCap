"""
Mock bot — simulates the real bot's behaviour using fake data.
Pushes updates to bot_state (same path the real bot uses).
Swap this out for the real TradingBot when API credentials are ready.
"""
import asyncio
import logging
import random

from api.state import bot_state
from data.models import TradeSignal
from storage.db import TradeDB

logger = logging.getLogger(__name__)

_SYMBOLS = ["R_75", "R_50", "R_100"]
_DIRECTIONS = ["CALL", "PUT"]
_TRENDS = ["UPTREND", "DOWNTREND", "RANGE"]
_ZONES = ["DEMAND", "SUPPLY", "NONE"]
_WIN_RATE = 0.56          # simulated edge
_PAYOUT_RATIO = 0.85      # 85% payout on win
_SIGNAL_INTERVAL = (8, 18)   # seconds between signals
_TRADE_DURATION = (5, 12)    # seconds a trade stays open


class MockBot:
    def __init__(self):
        self._db = TradeDB()
        self._db.connect()
        self._trade_counter = 0

    async def run(self) -> None:
        self._init_state()
        await bot_state.broadcast("snapshot", self._snapshot())
        logger.info("MockBot started — generating fake signals and trades")

        while bot_state.running:
            await asyncio.sleep(random.uniform(*_SIGNAL_INTERVAL))
            signal = self._make_signal()
            bot_state.last_signal = signal

            await bot_state.broadcast("signal", {
                "symbol": signal.symbol,
                "direction": signal.direction,
                "score": signal.score,
                "reason": signal.reason,
                "trend": signal.trend,
                "zone": signal.zone,
                "rsi": round(signal.rsi, 2),
            })

            if signal.direction != "NONE":
                asyncio.create_task(self._execute_trade(signal))

    def _init_state(self) -> None:
        bot_state.running = True
        bot_state.balance = 10_000.0
        bot_state.currency = "USD"
        bot_state.account_id = "DEMO-99999"
        bot_state.is_virtual = True
        bot_state.session_pnl = 0.0
        bot_state.wins = 0
        bot_state.losses = 0
        bot_state.total_trades = 0
        bot_state.consecutive_losses = 0
        bot_state.cb_tripped = False

    def _make_signal(self) -> TradeSignal:
        score = random.randint(0, 5)
        direction = random.choice(_DIRECTIONS) if score >= 3 else "NONE"
        rsi = random.uniform(15, 85)
        trend = random.choice(_TRENDS)
        zone = random.choice(_ZONES)

        parts = []
        if trend in ("UPTREND", "DOWNTREND"):
            parts.append(f"structure {trend}")
        if zone in ("DEMAND", "SUPPLY"):
            parts.append(f"price at {zone.lower()} zone")
        if rsi < 35:
            parts.append(f"RSI oversold ({rsi:.1f})")
        elif rsi > 65:
            parts.append(f"RSI overbought ({rsi:.1f})")
        if not parts:
            parts.append("monitoring — no confluence yet")

        return TradeSignal(
            symbol=random.choice(_SYMBOLS),
            direction=direction,
            score=score,
            reason=", ".join(parts),
            trend=trend,
            zone=zone,
            rsi=rsi,
            stake=round(bot_state.balance * 0.01, 2),
        )

    async def _execute_trade(self, signal: TradeSignal) -> None:
        self._trade_counter += 1
        contract_id = 100_000 + self._trade_counter
        stake = round(bot_state.balance * 0.01, 2)
        signal.stake = stake

        self._db.log_open(contract_id, signal)
        await asyncio.sleep(random.uniform(*_TRADE_DURATION))

        is_win = random.random() < _WIN_RATE
        profit = round(stake * _PAYOUT_RATIO if is_win else -stake, 2)

        bot_state.balance = round(bot_state.balance + profit, 2)
        bot_state.session_pnl = round(bot_state.session_pnl + profit, 2)
        bot_state.total_trades += 1

        if is_win:
            bot_state.wins += 1
            bot_state.consecutive_losses = 0
        else:
            bot_state.losses += 1
            bot_state.consecutive_losses += 1
            if bot_state.consecutive_losses >= 5:
                bot_state.cb_tripped = True
                bot_state.cb_reason = f"5 consecutive losses"

        total = bot_state.wins + bot_state.losses
        bot_state.win_rate = round(bot_state.wins / total, 4) if total > 0 else 0

        self._db.log_close(contract_id, profit, is_win)

        await bot_state.broadcast("trade_closed", {
            "contract_id": contract_id,
            "direction": signal.direction,
            "symbol": signal.symbol,
            "stake": stake,
            "profit": profit,
            "is_win": is_win,
            "balance": bot_state.balance,
            "session_pnl": bot_state.session_pnl,
            "wins": bot_state.wins,
            "losses": bot_state.losses,
            "win_rate": bot_state.win_rate,
        })

        await bot_state.broadcast("status_update", self._snapshot())

        result = "WIN" if is_win else "LOSS"
        logger.info(
            f"[MOCK] {signal.direction} {signal.symbol} → {result} "
            f"${profit:+.2f} | Balance: ${bot_state.balance:.2f}"
        )

    def _snapshot(self) -> dict:
        return {
            "running": bot_state.running,
            "balance": bot_state.balance,
            "session_pnl": bot_state.session_pnl,
            "wins": bot_state.wins,
            "losses": bot_state.losses,
            "win_rate": bot_state.win_rate,
            "cb_tripped": bot_state.cb_tripped,
            "cb_reason": bot_state.cb_reason,
        }
