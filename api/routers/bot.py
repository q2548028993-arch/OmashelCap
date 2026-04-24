import asyncio
import logging
import os

from fastapi import APIRouter, HTTPException

from api.state import bot_state

logger = logging.getLogger(__name__)
router = APIRouter()

USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"


@router.get("/status")
async def get_status():
    total = bot_state.wins + bot_state.losses
    return {
        "running": bot_state.running,
        "balance": bot_state.balance,
        "currency": bot_state.currency,
        "account_id": bot_state.account_id,
        "is_virtual": bot_state.is_virtual,
        "mock_mode": USE_MOCK,
        "circuit_breaker": {
            "tripped": bot_state.cb_tripped,
            "reason": bot_state.cb_reason,
            "consecutive_losses": bot_state.consecutive_losses,
        },
        "session": {
            "total_trades": total,
            "wins": bot_state.wins,
            "losses": bot_state.losses,
            "pnl": round(bot_state.session_pnl, 2),
            "win_rate": round(bot_state.wins / total, 4) if total > 0 else 0,
        },
    }


@router.post("/start")
async def start_bot():
    if bot_state.running:
        raise HTTPException(status_code=409, detail="Bot is already running")

    if USE_MOCK:
        from mock.bot import MockBot
        bot = MockBot()
    else:
        from main import TradingBot
        bot = TradingBot()

    bot_state._task = asyncio.create_task(bot.run())
    logger.info(f"Bot started ({'mock' if USE_MOCK else 'live'})")
    return {"status": "started", "mode": "mock" if USE_MOCK else "live"}


@router.post("/stop")
async def stop_bot():
    if not bot_state.running:
        raise HTTPException(status_code=409, detail="Bot is not running")
    await bot_state.stop()
    logger.info("Bot stopped")
    return {"status": "stopped"}
