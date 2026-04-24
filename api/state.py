import asyncio
from dataclasses import dataclass, field
from typing import Optional

from data.models import TradeSignal


@dataclass
class BotState:
    running: bool = False
    balance: float = 0.0
    currency: str = "USD"
    account_id: Optional[str] = None
    is_virtual: bool = True

    # Circuit breaker
    cb_tripped: bool = False
    cb_reason: str = ""
    consecutive_losses: int = 0

    # Session stats
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    session_pnl: float = 0.0

    # Latest signal
    last_signal: Optional[TradeSignal] = None

    # Internal
    _ws_clients: list = field(default_factory=list)
    _task: Optional[asyncio.Task] = None

    async def broadcast(self, event: str, data: dict) -> None:
        dead = []
        for client in list(self._ws_clients):
            try:
                await client.send_json({"event": event, "data": data})
            except Exception:
                dead.append(client)
        for c in dead:
            self._ws_clients.remove(c)

    def register_ws(self, client) -> None:
        self._ws_clients.append(client)

    def unregister_ws(self, client) -> None:
        if client in self._ws_clients:
            self._ws_clients.remove(client)

    async def stop(self) -> None:
        self.running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass


bot_state = BotState()
