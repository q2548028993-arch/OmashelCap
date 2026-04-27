"""
OmashelCap Trading Bot — Entry Point
Wires: WebSocket client → data feed → signal engine → risk manager → order manager
"""

import asyncio
import logging
import sys

from config.settings import settings
from core.client import DerivClient
from core.router import MessageRouter
from core.session import Session
from data.feed import DataFeed
from data.models import Candle, TradeSignal
from data.store import DataStore
from notify.telegram import TelegramNotifier
from risk.circuit_breaker import CircuitBreaker
from risk.manager import RiskManager
from storage.db import TradeDB
from strategies.structure_confluence import StructureConfluenceStrategy
from trading.order import OrderManager
from trading.tracker import TradeTracker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log"),
    ],
)
logger = logging.getLogger(__name__)


class TradingBot:
    def __init__(self):
        settings.validate()

        # Core
        self.router = MessageRouter()
        self.client = DerivClient(on_message=self.router.dispatch)
        self.session = Session()

        # Data
        self.store = DataStore(symbol=settings.SYMBOL)
        self.feed: DataFeed | None = None

        # Analysis
        self.strategy = StructureConfluenceStrategy()

        # Risk
        self.risk_manager: RiskManager | None = None
        self.circuit_breaker: CircuitBreaker | None = None

        # Trading
        self.order_manager = OrderManager(send_fn=self.client.send)
        self.tracker = TradeTracker()

        # Infrastructure
        self.db = TradeDB()
        self.notifier = TelegramNotifier()

    async def run(self) -> None:
        self.db.connect()
        logger.info(
            f"Starting OmashelCap Bot | Symbol: {settings.SYMBOL} | Mode: {settings.TRADING_MODE}"
        )

        # Register message handlers
        self.router.register("authorize", self._on_authorize)
        self.router.register("balance", self._on_balance)
        self.router.register("candles", self._on_candles)
        self.router.register("ohlc", self._on_ohlc)
        self.router.register("tick", self._on_tick)
        self.router.register("proposal", self._on_proposal)
        self.router.register("buy", self._on_buy)
        self.router.register("proposal_open_contract", self._on_proposal_open_contract)

        # Start WebSocket (runs until stopped)
        await asyncio.gather(
            self.client.connect(),
            self._startup_sequence(),
        )

    async def _startup_sequence(self) -> None:
        await self.client.wait_connected()
        await self.session.authorize(self.client.send)
        await self.session.wait_authorized()

        # Subscribe to balance updates
        await self.client.send({"balance": 1, "subscribe": 1})

        # Initialize risk components
        self.risk_manager = RiskManager(self.session.balance)
        self.circuit_breaker = CircuitBreaker(self.session.balance)

        # Initialize data feed
        self.feed = DataFeed(
            store=self.store,
            send_fn=self.client.send,
            on_candle_update=self._on_candle_close,
        )
        await self.feed.start()
        await self.feed.wait_initialized()

        logger.info("Bot fully initialized — watching for signals...")

    # ── Message handlers ──────────────────────────────────────────────────────

    def _on_authorize(self, msg: dict) -> None:
        self.session.on_authorize(msg)

    def _on_balance(self, msg: dict) -> None:
        self.session.on_balance(msg)
        if self.risk_manager:
            self.risk_manager.update_balance(self.session.balance)

    def _on_candles(self, msg: dict) -> None:
        if self.feed:
            self.feed.on_candles(msg)

    def _on_ohlc(self, msg: dict) -> None:
        if self.feed:
            self.feed.on_ohlc(msg)

    def _on_tick(self, msg: dict) -> None:
        if self.feed:
            self.feed.on_tick(msg)

    def _on_proposal(self, msg: dict) -> None:
        asyncio.create_task(self.order_manager.on_proposal(msg))

    def _on_buy(self, msg: dict) -> None:
        self.order_manager.on_buy(msg)
        buy = msg.get("buy", {})
        contract_id = buy.get("contract_id")
        if contract_id and self.order_manager._active_signal:
            self.tracker.open(contract_id, self.order_manager._active_signal)
            self.db.log_open(contract_id, self.order_manager._active_signal)
            asyncio.create_task(
                self.notifier.trade_opened(
                    direction=self.order_manager._active_signal.direction,
                    stake=self.order_manager._active_signal.stake,
                    score=self.order_manager._active_signal.score,
                    reason=self.order_manager._active_signal.reason,
                )
            )

    def _on_proposal_open_contract(self, msg: dict) -> None:
        self.order_manager.on_proposal_open_contract(msg)

    # ── Signal evaluation (called on each new candle) ─────────────────────────

    def _on_candle_close(self, candle: Candle) -> None:
        if not self.circuit_breaker or not self.risk_manager:
            return

        if self.circuit_breaker.is_tripped:
            logger.warning(f"Circuit breaker active: {self.circuit_breaker.trip_reason}")
            return

        if self.order_manager.is_in_trade:
            return

        signal = self.strategy.evaluate(self.store)

        logger.info(
            f"Signal | {signal.direction} | score={signal.score} | "
            f"trend={signal.trend} | zone={signal.zone} | "
            f"RSI={signal.rsi:.1f} | {signal.reason}"
        )

        if signal.direction != "NONE":
            signal.stake = self.risk_manager.compute_stake()
            asyncio.create_task(self.order_manager.request_proposal(signal))

    # ── Trade result callback ─────────────────────────────────────────────────

    def _on_trade_closed(
        self,
        contract_id: int,
        profit: float,
        is_win: bool,
        signal: TradeSignal | None,
    ) -> None:
        self.tracker.close(contract_id, profit, is_win)
        self.db.log_close(contract_id, profit, is_win)

        assert self.circuit_breaker is not None
        if is_win:
            self.circuit_breaker.on_win()
        else:
            self.circuit_breaker.on_loss(self.session.balance)
            if self.circuit_breaker.is_tripped:
                asyncio.create_task(self.notifier.circuit_tripped(self.circuit_breaker.trip_reason))

        direction = signal.direction if signal else "?"
        asyncio.create_task(
            self.notifier.trade_closed(
                direction=direction,
                profit=profit,
                win_rate=self.tracker.win_rate,
                total_pnl=self.tracker.total_profit,
            )
        )
        logger.info(self.tracker.session_summary())


async def main():
    bot = TradingBot()
    bot.order_manager.set_on_trade_close(bot._on_trade_closed)
    try:
        await bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        bot.db.close()
        logger.info(f"Final: {bot.tracker.session_summary()}")


if __name__ == "__main__":
    asyncio.run(main())
