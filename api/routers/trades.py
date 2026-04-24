import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Query

router = APIRouter()
DB_PATH = Path("trades.db")


def _get_conn():
    return sqlite3.connect(DB_PATH)


@router.get("/")
async def get_trades(
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
    direction: Optional[str] = None,
):
    if not DB_PATH.exists():
        return {"trades": [], "total": 0}

    conn = _get_conn()
    try:
        where = "WHERE closed_at IS NOT NULL"
        params: list = []
        if direction:
            where += " AND direction = ?"
            params.append(direction.upper())

        total = conn.execute(f"SELECT COUNT(*) FROM trades {where}", params).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT contract_id, symbol, direction, stake, score, reason,
                   trend, zone, rsi, profit, is_win, opened_at, closed_at
            FROM trades {where}
            ORDER BY closed_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        ).fetchall()

        trades = [
            {
                "contract_id": r[0], "symbol": r[1], "direction": r[2],
                "stake": r[3], "score": r[4], "reason": r[5],
                "trend": r[6], "zone": r[7], "rsi": r[8],
                "profit": r[9], "is_win": bool(r[10]),
                "opened_at": r[11], "closed_at": r[12],
            }
            for r in rows
        ]
        return {"trades": trades, "total": total}
    finally:
        conn.close()


@router.get("/summary")
async def get_summary():
    if not DB_PATH.exists():
        return {}

    conn = _get_conn()
    try:
        row = conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN is_win=1 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN is_win=0 THEN 1 ELSE 0 END) as losses,
                SUM(profit) as total_pnl,
                AVG(CASE WHEN is_win=1 THEN profit ELSE NULL END) as avg_win,
                AVG(CASE WHEN is_win=0 THEN profit ELSE NULL END) as avg_loss
            FROM trades WHERE closed_at IS NOT NULL
        """).fetchone()
        total = row[0] or 0
        return {
            "total_trades": total,
            "wins": row[1] or 0,
            "losses": row[2] or 0,
            "win_rate": round((row[1] or 0) / total, 4) if total > 0 else 0,
            "total_pnl": round(row[3] or 0, 2),
            "avg_win": round(row[4] or 0, 2),
            "avg_loss": round(row[5] or 0, 2),
        }
    finally:
        conn.close()
