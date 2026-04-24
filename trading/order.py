import asyncio
import logging
from typing import Callable, Optional

from config.settings import settings
from data.models import TradeSignal

logger = logging.getLogger(__name__)


class OrderManager:
    """
    Handles the full trade lifecycle: proposal → buy → monitor → result.
    One active trade at a time; new signals are dropped while a trade is open.
    """

    def __init__(self, send_fn: Callable):
        self._send = send_fn
        self._pending_proposal_id: Optional[str] = None
        self._active_contract_id: Optional[int] = None
        self._active_signal: Optional[TradeSignal] = None
        self._in_trade = asyncio.Event()
        self._on_trade_close: Optional[Callable] = None

    def set_on_trade_close(self, callback: Callable) -> None:
        self._on_trade_close = callback

    @property
    def is_in_trade(self) -> bool:
        return self._in_trade.is_set()

    async def request_proposal(self, signal: TradeSignal) -> None:
        if self.is_in_trade:
            logger.debug("Already in a trade — proposal skipped")
            return

        self._active_signal = signal
        logger.info(
            f"Requesting proposal | {signal.direction} {settings.SYMBOL} | "
            f"score={signal.score} | reason: {signal.reason}"
        )
        await self._send({
            "proposal": 1,
            "amount": signal.stake,
            "basis": "stake",
            "contract_type": signal.direction,
            "currency": "USD",
            "duration": settings.TRADE_DURATION,
            "duration_unit": settings.TRADE_DURATION_UNIT,
            "symbol": settings.SYMBOL,
        })

    async def on_proposal(self, message: dict) -> None:
        proposal = message.get("proposal", {})
        proposal_id = proposal.get("id")
        ask_price = proposal.get("ask_price")

        if not proposal_id or self._active_signal is None:
            return

        logger.info(f"Proposal received | id={proposal_id} | ask_price={ask_price}")
        self._pending_proposal_id = proposal_id

        await self._send({
            "buy": proposal_id,
            "price": self._active_signal.stake,
        })

    def on_buy(self, message: dict) -> None:
        buy = message.get("buy", {})
        contract_id = buy.get("contract_id")
        buy_price = buy.get("buy_price")

        if not contract_id:
            logger.error(f"Buy failed: {message}")
            self._active_signal = None
            return

        self._active_contract_id = contract_id
        self._in_trade.set()
        logger.info(f"Trade open | contract_id={contract_id} | buy_price={buy_price}")

        asyncio.create_task(self._subscribe_contract(contract_id))

    async def _subscribe_contract(self, contract_id: int) -> None:
        await self._send({
            "proposal_open_contract": 1,
            "contract_id": contract_id,
            "subscribe": 1,
        })

    def on_proposal_open_contract(self, message: dict) -> None:
        poc = message.get("proposal_open_contract", {})
        if not poc:
            return

        status = poc.get("status")
        if status in ("sold", "won", "lost"):
            profit = float(poc.get("profit", 0))
            is_win = profit > 0
            logger.info(
                f"Trade closed | status={status} | profit={profit:.2f} | "
                f"contract_id={self._active_contract_id}"
            )
            self._close_trade(profit, is_win)

    def _close_trade(self, profit: float, is_win: bool) -> None:
        signal = self._active_signal
        contract_id = self._active_contract_id

        self._active_contract_id = None
        self._active_signal = None
        self._pending_proposal_id = None
        self._in_trade.clear()

        if self._on_trade_close:
            self._on_trade_close(contract_id, profit, is_win, signal)
