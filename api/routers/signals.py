from fastapi import APIRouter

from api.state import bot_state
from notify.telegram import TelegramNotifier

router = APIRouter()


@router.get("/latest")
async def get_latest_signal():
    sig = bot_state.last_signal
    if not sig:
        return {"signal": None}
    return {
        "signal": {
            "symbol": sig.symbol,
            "direction": sig.direction,
            "score": sig.score,
            "reason": sig.reason,
            "trend": sig.trend,
            "zone": sig.zone,
            "rsi": round(sig.rsi, 2),
        }
    }


@router.post("/test-telegram")
async def test_telegram():
    notifier = TelegramNotifier()
    if not notifier.enabled:
        return {"status": "disabled", "message": "TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set in .env"}
    await notifier.test_message()
    return {"status": "sent", "message": "Check your Telegram"}
