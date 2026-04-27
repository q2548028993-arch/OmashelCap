import logging
from dataclasses import dataclass
from datetime import datetime

from data.models import TradeSignal

logger = logging.getLogger(__name__)


@dataclass
class TradeRecord:
    contract_id: int
    signal: TradeSignal
    opened_at: datetime
    closed_at: datetime | None = None
    profit: float = 0.0
    is_win: bool = False

    @property
    def is_closed(self) -> bool:
        return self.closed_at is not None


class TradeTracker:
    """
    Keeps a session history of all trades and computes running stats.
    """

    def __init__(self):
        self._trades: list[TradeRecord] = []

    def open(self, contract_id: int, signal: TradeSignal) -> TradeRecord:
        record = TradeRecord(
            contract_id=contract_id,
            signal=signal,
            opened_at=datetime.utcnow(),
        )
        self._trades.append(record)
        return record

    def close(self, contract_id: int, profit: float, is_win: bool) -> TradeRecord | None:
        record = self._find(contract_id)
        if record:
            record.closed_at = datetime.utcnow()
            record.profit = profit
            record.is_win = is_win
        return record

    def _find(self, contract_id: int) -> TradeRecord | None:
        for t in self._trades:
            if t.contract_id == contract_id:
                return t
        return None

    # ── Stats ─────────────────────────────────────────────────────────────────

    @property
    def total_trades(self) -> int:
        return len([t for t in self._trades if t.is_closed])

    @property
    def wins(self) -> int:
        return len([t for t in self._trades if t.is_closed and t.is_win])

    @property
    def losses(self) -> int:
        return len([t for t in self._trades if t.is_closed and not t.is_win])

    @property
    def win_rate(self) -> float:
        if self.total_trades == 0:
            return 0.0
        return self.wins / self.total_trades

    @property
    def total_profit(self) -> float:
        return sum(t.profit for t in self._trades if t.is_closed)

    def session_summary(self) -> str:
        return (
            f"Trades: {self.total_trades} | "
            f"W/L: {self.wins}/{self.losses} | "
            f"Win rate: {self.win_rate * 100:.1f}% | "
            f"P&L: {self.total_profit:+.2f}"
        )
