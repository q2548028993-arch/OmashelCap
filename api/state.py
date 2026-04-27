import asyncio
import contextlib
from dataclasses import dataclass, field

from data.models import TradeSignal


@dataclass
class BotState:
    running: bool = False
    balance: float = 0.0
    currency: str = "USD"
    account_id: str | None = None
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
    last_signal: TradeSignal | None = None

    # Internal
    _ws_clients: list = field(default_factory=list)
    _task: asyncio.Task | None = None

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
            with contextlib.suppress(asyncio.CancelledError):
                await self._task


bot_state = BotState()
