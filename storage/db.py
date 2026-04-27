import logging
import sqlite3
from datetime import datetime
from pathlib import Path

from data.models import TradeSignal

logger = logging.getLogger(__name__)

DB_PATH = Path("trades.db")


class TradeDB:
    """
    Async SQLite trade log. Every trade is recorded with full signal context.
    """

    def __init__(self):
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> None:
        self._conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self._create_tables()
        logger.info(f"Trade database connected: {DB_PATH.resolve()}")

    def _create_tables(self) -> None:
        assert self._conn is not None
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_id     INTEGER,
                symbol          TEXT,
                direction       TEXT,
                stake           REAL,
                score           INTEGER,
                reason          TEXT,
                trend           TEXT,
                zone            TEXT,
                rsi             REAL,
                profit          REAL,
                is_win          INTEGER,
                opened_at       TEXT,
                closed_at       TEXT
            )
        """)
        self._conn.commit()

    def log_open(self, contract_id: int, signal: TradeSignal) -> int:
        assert self._conn is not None
        cursor = self._conn.execute(
            """
            INSERT INTO trades
                (contract_id, symbol, direction, stake, score, reason, trend, zone, rsi, opened_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                contract_id,
                signal.symbol,
                signal.direction,
                signal.stake,
                signal.score,
                signal.reason,
                signal.trend,
                signal.zone,
                signal.rsi,
                datetime.utcnow().isoformat(),
            ),
        )
        self._conn.commit()
        return cursor.lastrowid or 0

    def log_close(self, contract_id: int, profit: float, is_win: bool) -> None:
        assert self._conn is not None
        self._conn.execute(
            """
            UPDATE trades
            SET profit=?, is_win=?, closed_at=?
            WHERE contract_id=?
            """,
            (profit, int(is_win), datetime.utcnow().isoformat(), contract_id),
        )
        self._conn.commit()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
