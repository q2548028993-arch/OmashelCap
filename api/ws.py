from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.state import bot_state

ws_router = APIRouter()


@ws_router.websocket("/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    bot_state.register_ws(websocket)
    try:
        # Send initial state snapshot
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
        # Keep connection alive (client sends ping, we echo pong)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        bot_state.unregister_ws(websocket)
