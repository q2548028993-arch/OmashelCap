import asyncio
import logging
from typing import Callable, Optional

from config.settings import settings
from data.models import Candle, Tick
from data.store import DataStore

logger = logging.getLogger(__name__)


class DataFeed:
    """
    Manages subscriptions to ticks and candles from the Deriv API.
    Populates the DataStore and calls on_candle_update when new data arrives.
    """

    def __init__(
        self,
        store: DataStore,
        send_fn: Callable,
        on_candle_update: Optional[Callable] = None,
    ):
        self._store = store
        self._send = send_fn
        self._on_candle_update = on_candle_update
        self._tick_sub_id: Optional[str] = None
        self._candle_sub_id: Optional[str] = None
        self._initialized = asyncio.Event()

    async def start(self) -> None:
        await self._fetch_candle_history()
        await self._subscribe_ticks()
        await self._subscribe_candles()

    async def _fetch_candle_history(self) -> None:
        logger.info(f"Fetching candle history for {settings.SYMBOL}...")
        await self._send({
            "ticks_history": settings.SYMBOL,
            "count": settings.CANDLE_HISTORY_COUNT,
            "end": "latest",
            "style": "candles",
            "granularity": settings.CANDLE_GRANULARITY,
        })

    async def _subscribe_ticks(self) -> None:
        await self._send({
            "ticks": settings.SYMBOL,
            "subscribe": 1,
        })

    async def _subscribe_candles(self) -> None:
        await self._send({
            "ticks_history": settings.SYMBOL,
            "count": 1,
            "end": "latest",
            "style": "candles",
            "granularity": settings.CANDLE_GRANULARITY,
            "subscribe": 1,
        })

    # ── Handlers (registered with MessageRouter) ─────────────────────────────

    def on_candles(self, message: dict) -> None:
        candles_data = message.get("candles", [])
        symbol = message.get("echo_req", {}).get("ticks_history", settings.SYMBOL)
        granularity = message.get("echo_req", {}).get("granularity", settings.CANDLE_GRANULARITY)

        candles = [
            Candle(
                symbol=symbol,
                epoch=int(c["epoch"]),
                open=float(c["open"]),
                high=float(c["high"]),
                low=float(c["low"]),
                close=float(c["close"]),
                granularity=granularity,
            )
            for c in candles_data
        ]
        self._store.load_candles(candles)
        self._initialized.set()
        logger.info(f"Candle history loaded: {len(candles)} candles")

    def on_ohlc(self, message: dict) -> None:
        ohlc = message.get("ohlc", {})
        if not ohlc:
            return

        candle = Candle(
            symbol=ohlc.get("symbol", settings.SYMBOL),
            epoch=int(ohlc["open_time"]),
            open=float(ohlc["open"]),
            high=float(ohlc["high"]),
            low=float(ohlc["low"]),
            close=float(ohlc["close"]),
            granularity=int(ohlc.get("granularity", settings.CANDLE_GRANULARITY)),
        )
        self._store.update_candle(candle)

        if self._on_candle_update:
            self._on_candle_update(candle)

    def on_tick(self, message: dict) -> None:
        tick_data = message.get("tick", {})
        if not tick_data:
            return

        tick = Tick(
            symbol=tick_data.get("symbol", settings.SYMBOL),
            epoch=int(tick_data["epoch"]),
            quote=float(tick_data["quote"]),
            pip_size=float(tick_data.get("pip_size", 0.0001)),
        )
        self._store.add_tick(tick)

    async def wait_initialized(self) -> None:
        await self._initialized.wait()
