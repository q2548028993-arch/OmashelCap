import json
import logging

import websockets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.state import bot_state
from config.settings import settings

logger = logging.getLogger(__name__)
ws_router = APIRouter()


@ws_router.websocket("/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    bot_state.register_ws(websocket)
    try:
        await websocket.send_json(
            {
                "event": "snapshot",
                "data": {
                    "running": bot_state.running,
                    "balance": bot_state.balance,
                    "session_pnl": bot_state.session_pnl,
                    "wins": bot_state.wins,
                    "losses": bot_state.losses,
                    "cb_tripped": bot_state.cb_tripped,
                },
            }
        )
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        bot_state.unregister_ws(websocket)


@ws_router.websocket("/chart")
async def chart_ws(websocket: WebSocket, symbol: str = "R_75", granularity: int = 60):
    """Stream live OHLC candles from Deriv to the dashboard chart."""
    await websocket.accept()

    if not settings.APP_ID:
        await websocket.send_json({"type": "error", "message": "DERIV_APP_ID not configured"})
        await websocket.close()
        return

    deriv_url = f"wss://ws.derivws.com/websockets/v3?app_id={settings.APP_ID}"

    try:
        async with websockets.connect(deriv_url) as deriv:
            await deriv.send(
                json.dumps(
                    {
                        "ticks_history": symbol,
                        "adjust_start_time": 1,
                        "count": 120,
                        "end": "latest",
                        "granularity": granularity,
                        "style": "candles",
                        "subscribe": 1,
                        "req_id": 1,
                    }
                )
            )

            async for raw in deriv:
                msg = json.loads(raw)
                mtype = msg.get("msg_type")

                if mtype == "candles":
                    bars = [
                        {
                            "time": c["epoch"],
                            "open": float(c["open"]),
                            "high": float(c["high"]),
                            "low": float(c["low"]),
                            "close": float(c["close"]),
                        }
                        for c in msg.get("candles", [])
                    ]
                    await websocket.send_json({"type": "history", "bars": bars})

                elif mtype == "ohlc":
                    o = msg["ohlc"]
                    await websocket.send_json(
                        {
                            "type": "update",
                            "bar": {
                                "time": int(o["epoch"]),
                                "open": float(o["open"]),
                                "high": float(o["high"]),
                                "low": float(o["low"]),
                                "close": float(o["close"]),
                            },
                        }
                    )

                elif mtype == "error":
                    logger.warning("Deriv chart error for %s: %s", symbol, msg.get("error"))
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": msg.get("error", {}).get("message", "Unknown error"),
                        }
                    )
                    break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error("Chart WS error for %s/%ss: %s", symbol, granularity, e)
