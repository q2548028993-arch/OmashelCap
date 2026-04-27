import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backtest.engine import run as run_backtest
from storage.db import TradeDB

router = APIRouter()
_db = TradeDB()
_db.connect()


class BacktestRequest(BaseModel):
    symbol: str = Field(default="R_75")
    granularity: int = Field(default=60, description="Candle size in seconds")
    count: int = Field(default=2000, ge=200, le=5000, description="Number of historical candles")
    trade_duration_bars: int = Field(
        default=5, ge=1, le=60, description="Trade duration in candles"
    )
    starting_balance: float = Field(default=1000.0, ge=10.0)
    min_score: int = Field(default=3, ge=2, le=5)


@router.post("/run")
async def run(req: BacktestRequest):
    result = await run_backtest(
        symbol=req.symbol,
        granularity=req.granularity,
        count=req.count,
        trade_duration_bars=req.trade_duration_bars,
        starting_balance=req.starting_balance,
        min_score=req.min_score,
    )

    if result.get("total_trades", 0) > 0 and "error" not in result:
        result["trade_duration_bars"] = req.trade_duration_bars
        result["min_score"] = req.min_score
        run_id = _db.log_backtest(result)
        result["run_id"] = run_id

    return result


@router.get("/history")
async def history(limit: int = 20):
    rows = _db.get_backtest_history(limit=limit)
    runs = []
    for r in rows:
        r["equity_curve"] = json.loads(r.pop("equity_curve_json", "[]"))
        runs.append(r)
    return {"runs": runs}


@router.get("/history/{run_id}")
async def get_run(run_id: int):
    row = _db.get_backtest_run(run_id)
    if not row:
        raise HTTPException(status_code=404, detail="Run not found")
    row["equity_curve"] = json.loads(row.pop("equity_curve_json", "[]"))
    return row
