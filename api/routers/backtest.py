from fastapi import APIRouter
from pydantic import BaseModel, Field

from backtest.engine import run as run_backtest

router = APIRouter()

GRANULARITY_LABELS = {60: "1m", 300: "5m", 900: "15m", 3600: "1h"}


class BacktestRequest(BaseModel):
    symbol: str = Field(default="R_75")
    granularity: int = Field(default=60, description="Candle size in seconds")
    count: int = Field(default=2000, ge=200, le=5000, description="Number of historical candles")
    trade_duration_bars: int = Field(default=5, ge=1, le=60, description="Trade duration in candles")
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
    return result
