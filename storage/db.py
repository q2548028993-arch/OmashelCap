import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from data.models import TradeSignal

logger = logging.getLogger(__name__)

DB_PATH = Path("trades.db")


class TradeDB:
    """SQLite store for live trades and backtest run history."""

    def __init__(self):
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> None:
        self._conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()
        logger.info(f"Trade database connected: {DB_PATH.resolve()}")

    def _create_tables(self) -> None:
        assert self._conn is not None
        self._conn.executescript("""
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
            );

            CREATE TABLE IF NOT EXISTS backtest_runs (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                ran_at              TEXT NOT NULL,
                symbol              TEXT NOT NULL,
                granularity         INTEGER NOT NULL,
                candle_count        INTEGER NOT NULL,
                trade_duration_bars INTEGER NOT NULL,
                starting_balance    REAL NOT NULL,
                final_balance       REAL NOT NULL,
                min_score           INTEGER NOT NULL,
                total_trades        INTEGER NOT NULL,
                wins                INTEGER NOT NULL,
                losses              INTEGER NOT NULL,
                win_rate            REAL NOT NULL,
                total_pnl           REAL NOT NULL,
                roi_pct             REAL NOT NULL,
                profit_factor       REAL NOT NULL,
                expectancy          REAL NOT NULL,
                max_drawdown_pct    REAL NOT NULL,
                best_trade          REAL NOT NULL,
                worst_trade         REAL NOT NULL,
                max_consec_wins     INTEGER NOT NULL,
                max_consec_losses   INTEGER NOT NULL,
                elapsed_s           REAL NOT NULL,
                equity_curve_json   TEXT NOT NULL
            );
        """)
        self._conn.commit()

    # ── Live trade logging ────────────────────────────────────────────────────

    def log_open(self, contract_id: int, signal: TradeSignal) -> int:
        assert self._conn is not None
        cursor = self._conn.execute(
            """
            INSERT INTO trades
                (contract_id, symbol, direction, stake, score, reason,
                 trend, zone, rsi, opened_at)
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

    # ── Backtest result logging ───────────────────────────────────────────────

    def log_backtest(self, result: dict[str, Any]) -> int:
        assert self._conn is not None
        cursor = self._conn.execute(
            """
            INSERT INTO backtest_runs (
                ran_at, symbol, granularity, candle_count, trade_duration_bars,
                starting_balance, final_balance, min_score,
                total_trades, wins, losses, win_rate, total_pnl, roi_pct,
                profit_factor, expectancy, max_drawdown_pct,
                best_trade, worst_trade, max_consec_wins, max_consec_losses,
                elapsed_s, equity_curve_json
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                datetime.utcnow().isoformat(),
                result["symbol"],
                result["granularity"],
                result["candle_count"],
                result.get("trade_duration_bars", 0),
                result["starting_balance"],
                result["final_balance"],
                result.get("min_score", 3),
                result["total_trades"],
                result["wins"],
                result["losses"],
                result["win_rate"],
                result["total_pnl"],
                result["roi_pct"],
                result["profit_factor"] if result["profit_factor"] != float("inf") else 9999.0,
                result["expectancy_per_trade"],
                result["max_drawdown_pct"],
                result["best_trade"],
                result["worst_trade"],
                result["max_consec_wins"],
                result["max_consec_losses"],
                result["elapsed_s"],
                json.dumps(result.get("equity_curve", [])),
            ),
        )
        self._conn.commit()
        return cursor.lastrowid or 0

    def get_backtest_history(self, limit: int = 20) -> list[dict]:
        assert self._conn is not None
        rows = self._conn.execute(
            """
            SELECT id, ran_at, symbol, granularity, candle_count,
                   trade_duration_bars, starting_balance, final_balance, min_score,
                   total_trades, wins, losses, win_rate, total_pnl, roi_pct,
                   profit_factor, expectancy, max_drawdown_pct,
                   best_trade, worst_trade, max_consec_wins, max_consec_losses,
                   elapsed_s, equity_curve_json
            FROM backtest_runs
            ORDER BY ran_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_backtest_run(self, run_id: int) -> dict | None:
        assert self._conn is not None
        row = self._conn.execute(
            "SELECT * FROM backtest_runs WHERE id = ?", (run_id,)
        ).fetchone()
        return dict(row) if row else None

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def close(self) -> None:
        if self._conn:
            self._conn.close()
