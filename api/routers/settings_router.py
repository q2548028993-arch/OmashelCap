"""
Runtime settings update — changes take effect on the next bot start.
Values are stored in memory only; persist changes to .env manually.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from config.settings import settings

router = APIRouter()

VALID_SYMBOLS = [
    "R_10",
    "R_25",
    "R_50",
    "R_75",
    "R_100",
    "CRASH1000",
    "CRASH500",
    "BOOM1000",
    "BOOM500",
]
VALID_GRANULARITIES = [60, 300, 900, 3600]


class SettingsUpdate(BaseModel):
    symbol: str | None = None
    granularity: int | None = None
    risk_per_trade: float | None = Field(default=None, ge=0.005, le=0.05)
    min_stake: float | None = Field(default=None, ge=0.35)
    max_stake: float | None = Field(default=None, ge=1.0, le=500.0)
    trade_duration: int | None = Field(default=None, ge=1, le=60)
    max_consecutive_losses: int | None = Field(default=None, ge=2, le=20)


@router.get("/")
async def get_settings():
    return {
        "symbol": settings.SYMBOL,
        "granularity": settings.CANDLE_GRANULARITY,
        "risk_per_trade": settings.RISK_PER_TRADE,
        "min_stake": settings.MIN_STAKE,
        "max_stake": settings.MAX_STAKE,
        "trade_duration": settings.TRADE_DURATION,
        "trade_duration_unit": settings.TRADE_DURATION_UNIT,
        "max_consecutive_losses": settings.MAX_CONSECUTIVE_LOSSES,
        "daily_drawdown_limit": settings.DAILY_DRAWDOWN_LIMIT,
    }


@router.patch("/")
async def update_settings(update: SettingsUpdate):
    if update.symbol is not None:
        if update.symbol not in VALID_SYMBOLS:
            return {"error": f"Invalid symbol. Choose from: {VALID_SYMBOLS}"}
        settings.SYMBOL = update.symbol

    if update.granularity is not None:
        if update.granularity not in VALID_GRANULARITIES:
            return {"error": f"Invalid granularity. Choose from: {VALID_GRANULARITIES}"}
        settings.CANDLE_GRANULARITY = update.granularity

    if update.risk_per_trade is not None:
        settings.RISK_PER_TRADE = update.risk_per_trade

    if update.min_stake is not None:
        settings.MIN_STAKE = update.min_stake

    if update.max_stake is not None:
        settings.MAX_STAKE = update.max_stake

    if update.trade_duration is not None:
        settings.TRADE_DURATION = update.trade_duration

    if update.max_consecutive_losses is not None:
        settings.MAX_CONSECUTIVE_LOSSES = update.max_consecutive_losses

    return {
        "status": "updated",
        "settings": {
            "symbol": settings.SYMBOL,
            "granularity": settings.CANDLE_GRANULARITY,
            "risk_per_trade": settings.RISK_PER_TRADE,
            "min_stake": settings.MIN_STAKE,
            "max_stake": settings.MAX_STAKE,
            "trade_duration": settings.TRADE_DURATION,
            "max_consecutive_losses": settings.MAX_CONSECUTIVE_LOSSES,
        },
    }
