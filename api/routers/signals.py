from fastapi import APIRouter

from api.state import bot_state

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
