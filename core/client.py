import asyncio
import json
import logging
from typing import Callable, Optional

import websockets
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from config.settings import settings

logger = logging.getLogger(__name__)


class DerivClient:
    """
    Manages the WebSocket connection to Deriv API.
    Handles: connect, reconnect, heartbeat, send, receive.
    All bot logic sits above this layer.
    """

    def __init__(self, on_message: Callable[[dict], None]):
        self._on_message = on_message
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._connected = asyncio.Event()
        self._running = False
        self._req_id = 0

    def next_req_id(self) -> int:
        self._req_id += 1
        return self._req_id

    async def send(self, payload: dict) -> None:
        if self._ws is None or not self._connected.is_set():
            logger.warning("Send attempted while disconnected — queuing skipped")
            return
        payload.setdefault("req_id", self.next_req_id())
        await self._ws.send(json.dumps(payload))

    async def connect(self) -> None:
        self._running = True
        backoff = 1

        while self._running:
            try:
                logger.info("Connecting to Deriv API...")
                async with websockets.connect(settings.WS_URL) as ws:
                    self._ws = ws
                    self._connected.set()
                    backoff = 1
                    logger.info("Connected")

                    # Run heartbeat and receiver concurrently
                    await asyncio.gather(
                        self._heartbeat(),
                        self._receiver(),
                    )

            except (ConnectionClosedError, ConnectionClosedOK) as e:
                logger.warning(f"Connection closed: {e}")
            except Exception as e:
                logger.error(f"Connection error: {e}")
            finally:
                self._connected.clear()
                self._ws = None

            if self._running:
                logger.info(f"Reconnecting in {backoff}s...")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)

    async def _receiver(self) -> None:
        async for raw in self._ws:
            try:
                msg = json.loads(raw)
                if msg.get("msg_type") != "ping":
                    await asyncio.get_event_loop().run_in_executor(
                        None, self._on_message, msg
                    )
            except Exception as e:
                logger.error(f"Message handling error: {e}")

    async def _heartbeat(self) -> None:
        while self._connected.is_set():
            await asyncio.sleep(settings.PING_INTERVAL)
            await self.send({"ping": 1})

    async def wait_connected(self) -> None:
        await self._connected.wait()

    def stop(self) -> None:
        self._running = False
        if self._ws:
            asyncio.create_task(self._ws.close())
